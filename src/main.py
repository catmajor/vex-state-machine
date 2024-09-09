# Library imports
from vex import *

class DblLinkdListNode:
    def __init__(self, head, previous, next, data):
        self.HEAD = head
        self.previous = previous
        self.next = next
        self.data = data
    def remove(self):
        if (self.next==None):
            self.HEAD.End = self.previous
        self.previous.next = self.next
        if self.next:
            self.next.previous = self.previous
        self.next=None
        self.previous=None
    def append_to_end(self):
        self.HEAD.End.next = self
        self.previous = self.HEAD.End
        self.HEAD.End = self.HEAD.End.next
    def assign_state(self, state):
        self.state = state
class DblLinkedHead(DblLinkdListNode):
    def __init__(self):
        DblLinkdListNode.__init__(self, self, self, None, None)
        self.End = self
    def remove(self):
        pass

class PORTS:
    BRAIN = Brain()
    ONE = Motor(Ports.PORT1, GearSetting.RATIO_18_1, True) #left motor
    TWO = MessageLink(Ports.PORT2, "radio", VexlinkType.GENERIC)
    THREE = None
    FOUR = None
    FIVE = None
    SIX = Inertial(Ports.PORT6)
    SEVEN = None
    EIGHT = Motor(Ports.PORT8)
    NINE = None
    TEN = Motor(Ports.PORT10, GearSetting.RATIO_18_1, False)
    A = Light(BRAIN.three_wire_port.a)
    B = Light(BRAIN.three_wire_port.b)
    C = Bumper(BRAIN.three_wire_port.c)
    D = None
    E = None
    F = None
    G = Sonar(BRAIN.three_wire_port.g)
    H = G

#EventListener for EventHandler
class EventListener:
    def __init__(self, func: Callable[[], None], once = False):
        self.func = func
        self.once = once
        #self.__node = None
    def __call__(self):
        self.func()

class EventController:
    def __init__(self):
        self.HEAD = DblLinkedHead()
    def add(self, event):
        node = DblLinkdListNode(self.HEAD, None, None, event)
        node.append_to_end()
    def execute(self):
        if (self.HEAD.next):
            first = self.HEAD.next
            first.data.handle()
            first.remove()

EVENT_CONTROL = EventController()

#Adds all possible functions to this class, and adds to VEX's event system to all for
#mutable execution of events
class EventHandler:
    def __init__(self):
        self.scheduled = False
        self.HEAD = DblLinkedHead()
    #will return the node assigned to the listener in the handler linked list
    def addEventListener(self, func: Callable[[], None], once = False) -> DblLinkdListNode:
        listener = EventListener(func, once)
        node = DblLinkdListNode(self.HEAD, None, None, listener)
        listener.__node = node
        node.append_to_end()
        return node
    def removeEventListener(self, node) -> None:
        node.remove()
    def add(self):
        if (self.scheduled): return
        self.scheduled = True
        EVENT_CONTROL.add(self)
    def handle(self) -> None:
        self.scheduled = False
        head = self.HEAD.next
        while(head):
            head.data.__call__()
            prev = head
            if head.data.once:
                prev.remove()
            head = head.next
     
class EventDispatcher:
    def __init__(self, event_handler: EventHandler):
        self.event_handler = event_handler
    def check(self, condition: Callable[[], bool]):
        if (condition):
            self.event_handler.handle()

class CustomHandlerController():
    def __init__(self):
        self.HEAD = DblLinkedHead()
    def expect(self, custom_handler, once = False):
        custom_handler.expect(once)
    def stop_expecting(self, custom_handler):
        custom_handler.stop_expecting()
    def check_all_handlers(self):
        head = self.HEAD.next
        while(head):
            result = head.data.check()
            if (result and head.data.detected == False):
                head.data.dispatch()
                prev = head
                if head.data.once:
                    prev.data.stop_expecting()
            elif head.data.detected and result==False:
                head.data.detected = True
            head = head.next

HANDLER_CONTROLLER = CustomHandlerController()

class CustomHandler():
    def __init__(self, check_func: Callable[[], bool] = lambda: True):
        self.__node = DblLinkdListNode(HANDLER_CONTROLLER.HEAD, None, None, self)
        self.once = False
        self.expecting = False
        self.detected = False
        self.__check_func = check_func
        self.condition_reached = EventHandler()
    def check(self) -> bool:
        return self.__check_func()
    def dispatch(self):
        self.condition_reached.add()
    def expect(self, once = False):
        if (self.expecting): return
        self.expecting = True
        self.once = once
        self.__node.append_to_end()
    def stop_expecting(self):
        self.expecting = False
        self.__node.remove()


#specific event handler for buttons, takes in the Bumper vex object and creates
#the event handlers for press and release      
class ButtonHandler():
    def __init__(self, port: Bumper):
        self.button = port
        self.pressed = EventHandler()
        self.released = EventHandler()
        self.button.pressed(self.pressed.add)
        self.button.released(self.released.add)

BUTTON_C = ButtonHandler(PORTS.C)

class IMUHandler():
    def __init__(self, port: Inertial):
        self.imu = port
        self.collision = EventHandler()
        self.imu.collision(self.collision.add)

IMU_6 = IMUHandler(PORTS.SIX)

class UltrasonicHandler():
    def __init__(self, port: Sonar):
        self.sonar = port

ULTRASONIC_G = UltrasonicHandler(PORTS.G)


class MotorHandler():
    def __init__(self, port: Motor):
        self.motor = port
        self.on_finish = EventHandler()
        self.dispatcher = EventDispatcher(self.on_finish)



STATEHEAD = DblLinkedHead()
#useful metrics for determining states. If theres a mismatch, then there is a loose state on somewhere
active_states_estimate = 0
active_states_actual = 0
#State definition
#defines state behavior when enabled/disabled
#doesn't dictate at all whether state will automatically disable or enable

class State():
    def __init__(self, name: str, next):
        self.name = name
        self.__next = next
        self.__node = DblLinkdListNode(STATEHEAD, None, None, self)
        self.__active = False
    def enable(self):
        if (self.__active): return
        self.__active = True
        self.__node.append_to_end()
        global active_states_estimate
        active_states_estimate = active_states_estimate+1
    def act(self):
        pass
    def disable(self):
        if (not self.__active): return
        self.__active = False
        global active_states_estimate
        active_states_estimate = active_states_estimate-1
        PORTS.BRAIN.screen.set_pen_color(Color.BLACK)
        PORTS.BRAIN.screen.draw_rectangle(0, 0, 480, 22, Color.BLACK)
        PORTS.BRAIN.screen.set_pen_color(Color.WHITE)
        PORTS.BRAIN.screen.print_at(self.to_string() + " -> " + self.__next.to_string(), x=0, y=18)
        self.__node.remove()
    def to_string(self):
        return self.name
    def active(self):
        return self.__active
    def set_next(self, next):
        self.__next = next


class StateList:
    def __init__(self, list):
        self.list = list
    def enable(self):
        for state in self.list:
            state.enable()

#end, default state. When this state is enabled, it should disable all other states currently active
class END_STATE(State):
    def __init__(self):
        State.__init__(self, "END", None)
    def enable(self):
        STATEHEAD.next = None
    def act(self):
        self.disable()
    def disable(self):
        STATEHEAD.next = None
        #disable all processes in process handler
    def to_string(self):
        return "END"

END = END_STATE()

#test idle state
class IDLE_STATE(State):
    def __init__(self, button: ButtonHandler, next = END):
        State.__init__(self, "IDLE", next)
        self.button = button
        self.vary = False
    def enable(self):
        State.enable(self)
        self.listener = self.button.pressed.addEventListener(self.disable, once=True)
    def disable(self):
        State.disable(self)
        #self.button.pressed.removeEventListener(self.handler)
        self.__next.enable()

#second test idle state
class IDLE_STATE2(State):
    def __init__(self, button: ButtonHandler, next = END):
        State.__init__(self, "IDLE2", next)
        self.button = button
        self.listener = None
        self.vary = False
    def enable(self):
        State.enable(self)
        self.listener = self.button.pressed.addEventListener(self.disable, once=True)
    def disable(self):
        State.disable(self)
        #self.button.pressed.removeEventListener(self.handler)
        self.__next.enable()

program_time = 0

class ROBOT_METRICS_STATE(State):
    def __init__(self, next = END):
        State.__init__(self, "BUTTON_DISPLAY", next)
        self.count = 0
        self.handler = None
        self.button = BUTTON_C
        self.brain = PORTS.BRAIN
    def enable(self):
        State.enable(self)
        self.handler = self.button.pressed.addEventListener(self.on_press)
        #vex screen is 480x272 pixels
    def act(self):
        self.brain.screen.set_pen_color(Color.WHITE)
        self.brain.screen.draw_rectangle(0, 22, 480, 250, Color.BLACK)
        self.x = 10
        self.y = 42
        self.brain.screen.set_pen_color(Color.BLUE)
        self.print("Program cycles:")
        self.print(str(program_time))
        self.print("Active States (Est):")
        self.print(str(active_states_estimate))
        self.print("Active States (Act):")
        self.print(str(active_states_actual))
        self.print("Button Presses:")
        self.print(str(self.count))
        self.print("Rotation:")
        self.print(str(IMU_6.imu.rotation()))
        self.print("Distance in front:")
        self.print(str(ULTRASONIC_G.sonar.distance(DistanceUnits.CM)))
    def disable(self):
        State.disable(self)
        self.button.pressed.removeEventListener(self.handler)
    def on_press(self):
        self.count = self.count+1
    def print(self, text):
        self.brain.screen.print_at(text, x = self.x, y = self.y, opaque = False)
        self.y = self.y+20
        if self.y>=240:
            self.y = 42
            self.x = 250
# define the states
      
class TURN_STATE(State):
    def __init__(self, motor_left: Motor, motor_right: Motor, imu: IMUHandler, target_angle, stop_handler: CustomHandler, ):
        State.__init__(self, "TURN", next = END)
        self.motor_left = motor_left
        self.motor_right = motor_right
        self.imu = imu
        self.target_angle = target_angle
        self.stop_handler = stop_handler
        self.stop_listener = None
        self.button_listener = None
    def enable(self):
        State.enable(self)
        self.motor_left.spin(DirectionType.REVERSE)
        self.motor_right.spin(DirectionType.FORWARD)
        self.stop_handler.expect()
        self.button_listener = BUTTON_C.pressed.addEventListener(self.disable)
        self.stop_listener = self.stop_handler.condition_reached.addEventListener(self.disable)
    def act(self):
        GAIN = 60
        error = self.target_angle - self.imu.imu.rotation()
        self.motor_left.set_velocity(GAIN*self.gain_function(error))
        self.motor_right.set_velocity(-GAIN*self.gain_function(error))
        PORTS.BRAIN.screen.print_at(str(self.target_angle - self.imu.imu.rotation()), x=10, y=130)
    def disable(self):
        State.disable(self)
        self.stop_handler.stop_expecting()
        self.stop_handler.condition_reached.removeEventListener(self.stop_listener)
        self.motor_right.stop()
        self.motor_left.stop()
        self.__next.enable()
        BUTTON_C.pressed.removeEventListener(self.button_listener)
    def gain_function(self, x): #use x/(x+10) so that for large values of degrees velocity isnt insane, also use only positive values of x
        sgn = math.copysign(1, x)
        pos = abs(x)
        return sgn*pos/(pos+10)
    
TURN_AFTER_DRIVE = TURN_STATE(PORTS.ONE, PORTS.TEN, IMU_6, -180, CustomHandler(lambda: abs(IMU_6.imu.heading()-180)<0.5))

class DRIVE_STATE(State):
    class Direction:
        FORWARD = 1
        BACKWARD = -1
    def __init__(self, motor_left: Motor, motor_right: Motor, direction, target_angle, stop_handler: CustomHandler, button: ButtonHandler):
        State.__init__(self, "DRIVE", next = END)
        self.motor_left = motor_left
        self.motor_right = motor_right
        self.button_listener = None
        self.button_handler = button
        self.stop_handler = stop_handler
        self.stop_listener = None
        self.direction = direction
        self.turned = False
        self.disable_handler = None
        self.target_angle = target_angle
    def enable(self):
        State.enable(self)
        self.button_listener = self.button_handler.pressed.addEventListener(self.disable)
        self.stop_handler.expect()
        self.stop_listener = self.stop_handler.condition_reached.addEventListener(self.disable)
        self.motor_left.spin(DirectionType.FORWARD)
        self.target_angle = IMU_6.imu.rotation()
        self.motor_right.spin(DirectionType.FORWARD)
    def act(self):
        error = IMU_6.imu.rotation() - self.target_angle
        GAIN = 1.2
        effort = error*GAIN
        self.motor_left.set_velocity(40*self.direction - effort, VelocityUnits.RPM)
        self.motor_right.set_velocity(40*self.direction + effort, VelocityUnits.RPM)
    def disable(self):
        self.motor_left.stop()
        self.motor_right.stop()
        self.stop_handler.stop_expecting()
        self.button_handler.pressed.removeEventListener(self.button_listener)
        self.stop_handler.condition_reached.removeEventListener(self.stop_listener)
        State.disable(self)
        self.__next.enable()


ROBOT_CLOSE = CustomHandler(lambda: ULTRASONIC_G.sonar.distance(DistanceUnits.CM)<8)

class HAIL_MARY_DRIVE_STATE(DRIVE_STATE):
    def __init__(self, motor_left: Motor, motor_right: Motor, target_angle_override = 0):
        DRIVE_STATE.__init__(self, motor_left, motor_right, DRIVE_STATE.Direction.FORWARD, 0, ROBOT_CLOSE, BUTTON_C)
        self.target_angle_override = target_angle_override
    def enable(self):
        DRIVE_STATE.enable(self)
        self.target_angle = self.target_angle_override


FIRST_DRIVE = HAIL_MARY_DRIVE_STATE(PORTS.ONE, PORTS.TEN)
SECOND_DRIVE = HAIL_MARY_DRIVE_STATE(PORTS.ONE, PORTS.TEN, -180)


class DRIVE_BACK_STATE(DRIVE_STATE):
    def __init__(self, motor_left: Motor, motor_right: Motor):
        DRIVE_STATE.__init__(self, motor_left, motor_right, DRIVE_STATE.Direction.BACKWARD, 0, CustomHandler(self.target_reached), BUTTON_C)
        self.name = "DRIVE_BACK"
        self.stop_handler.__check_func = self.target_reached
        self.left_initial = self.motor_left.position()
        self.right_initial = self.motor_right.position()
    def enable(self):
        DRIVE_STATE.enable(self)
        self.left_initial = self.motor_left.position()
        self.right_initial = self.motor_right.position()
    def target_reached(self) -> bool:
        return abs(self.motor_left.position()-self.left_initial)>1800 and abs(self.motor_right.position()-self.right_initial)>1800
DRIVE_BACK = DRIVE_BACK_STATE(PORTS.ONE, PORTS.TEN)




# Brain should be defined by default

# Robot configuration code



print("Running :)")

"""
Pro-tip: print out upon state transistions.

def handleButton(self):
    global current_state
    light_value = lightB.value()
    light_brightness = lightB.brightness()
    brain.screen.print_at("The current light sensor metrics:", x=10, y=100)
    brain.screen.print_at("Value: " + str(light_value), x=10, y=120)
    brain.screen.print_at("Brightness: " + str(light_brightness), x=10, y=140)
    self.disable()
"""

IMU_6.imu.calibrate()
while(IMU_6.imu.is_calibrating()):
    sleep(0.2, SECONDS)
IMU_6.imu.set_rotation(0, RotationUnits.DEG)
IDLE = IDLE_STATE(BUTTON_C)
IDLE2 = IDLE_STATE2(BUTTON_C)
METRICS = ROBOT_METRICS_STATE()
IDLE2.set_next(IDLE)
IDLE.set_next(FIRST_DRIVE)
FIRST_DRIVE.set_next(DRIVE_BACK)
DRIVE_BACK.set_next(TURN_AFTER_DRIVE)
TURN_AFTER_DRIVE.set_next(SECOND_DRIVE)
SECOND_DRIVE.set_next(IDLE2)
METRICS.enable()
IDLE.enable()

"""
The line below makes use of VEX's built-in event management. Basically, you set up a "callback", 
basically, a function that gets called whenever the button is pressed (there's a corresponding
one for released). Whenever the button is pressed, the handleButton function will get called,
_without you having to do anything else_.

"""

def length():
    count = 0
    head = STATEHEAD
    while (head!=None):
        count = count +1
        head = head.next
    return count
#buttonD.pressed(handleButton)

"""
Note that the main doesn't "do" anything. That is because the event (button press) is captured
automatically. So we have an empty main program!!!
"""
# The main loop

while True:
    active_states_actual = length() - 1
    HANDLER_CONTROLLER.check_all_handlers()
    EVENT_CONTROL.execute()
    runner_head = STATEHEAD.next
    while (runner_head!=None):
        runner_head.data.act()
        runner_head = runner_head.next
    program_time = program_time + 1
    sleep(0.2, SECONDS)

