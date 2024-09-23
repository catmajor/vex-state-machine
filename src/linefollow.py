# Library imports
#This code is very uncommented, hopefully the naming gives some clue to what it does
#Good Luck :)
#theres still a lot of stuff missing from the framework but in general its in a working condition
#yes some things can use a queue, but im too starved on time to implement the structure when a double linked list works just fine
#a linked list in general can be used as a queue if you keep track of the end node anyway
#program does its best to mimic the state paradigm covered in class
from vex import *

#forward declare states
CAMERA_CONTROL = None
DRIVE_BACK = None
DRIVE_BACK_AT_END = None
IDLE = None
METRICS = None
START = None
FIRST_DRIVE = None
TURN_AFTER_DRIVE = None
SECOND_DRIVE = None
TURN_AFTER_SECOND_DRIVE = None
FRUIT_APPROACH = None
FRUIT_SEARCH = None


class DblLinkdListNode:
    def __init__(self, head, previous, next, data):
        self.HEAD = head
        self.previous = previous
        self.next = next
        self.data = data
    def remove(self):
        if (self.next==None and self.previous):
            self.HEAD.End = self.previous
        if self.previous: 
            self.previous.next = self.next
        if self.next:
            self.next.previous = self.previous
        self.next=None
        self.previous=None
    def append_to_end(self):
        self.HEAD.End.next = self
        self.previous = self.HEAD.End
        self.HEAD.End = self
    def assign_state(self, state):
        self.state = state
class DblLinkedHead(DblLinkdListNode):
    def __init__(self):
        DblLinkdListNode.__init__(self, self, self, None, None)
        self.End = self
    def remove(self):
        pass
class CAMERA_VALUES:
    GREEN_FRUIT_CLOSE = Signature (1, -6881, -6331, -6606, -4169, -3611, -3890, 2.5, 0)
    GREEN_FRUIT_FAR = Signature (2, -4999, -4359, -4679, -4443, -4113, -4278, 2.5, 0)
    YELLOW_FRUIT_CLOSE = Signature (3, 1529, 2189, 1859, -4407, -4095, -4251, 2.5, 0)
    YELLOW_FRUIT_FAR = Signature (4, 4005, 4287, 4146, -4167, -4013, -4090, 2.5, 0)
    ORANGE_FRUIT_CLOSE = Signature (5, 767, 4935, 2851, -4009, -3573, -3791, 2.5, 0)
    ORANGE_FRUIT_FAR = Signature (6, 7971, 8385, 8178, -2879, -2731, -2805, 2.5, 0)


class PORTS:
    BRAIN = Brain()
    ONE = Motor(Ports.PORT1, GearSetting.RATIO_18_1, True) #left motor
    TWO = MessageLink(Ports.PORT2, "radio", VexlinkType.GENERIC)
    THREE = None
    FOUR = None
    FIVE = Vision(
            Ports.PORT5, 
            50, 
            CAMERA_VALUES.GREEN_FRUIT_CLOSE,
            CAMERA_VALUES.GREEN_FRUIT_FAR,
            CAMERA_VALUES.YELLOW_FRUIT_CLOSE,
            CAMERA_VALUES.YELLOW_FRUIT_FAR,
            CAMERA_VALUES.ORANGE_FRUIT_CLOSE,
            CAMERA_VALUES.ORANGE_FRUIT_FAR,
            )
    SIX = Inertial(Ports.PORT6)
    SEVEN = None
    EIGHT = Motor(Ports.PORT8, GearSetting.RATIO_18_1, False)
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

class Handler():
    def __init__(self):
        self.event = EventHandler()
    def addEventListener(self, func: Callable[[], None], once = False):
        return self.event.addEventListener(func, once)
    def removeEventListener(self, node):
        self.event.removeEventListener(node)

class CustomHandler(Handler):
    def __init__(self, check_func: Callable[[], bool] = lambda: True):
        Handler.__init__(self)
        self.__node = DblLinkdListNode(HANDLER_CONTROLLER.HEAD, None, None, self)
        self.once = False
        self.expecting = False
        self.detected = False
        self.__check_func = check_func
    def check(self) -> bool:
        return self.__check_func()
    def dispatch(self):
        self.event.add()
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

class SensorHandler(Handler):
    def __init__(self, sensor_func):
        Handler.__init__(self)
        sensor_func(self.event.add)

#for handlers that have pairs, i.e. 
def pair_handlers(handler1: CustomHandler, handler2: CustomHandler):
    def listener1():
        handler1.stop_expecting()
        handler2.expect()
    def listener2():
        handler2.stop_expecting()
        handler1.expect()
    handler1.addEventListener(listener1)
    handler2.addEventListener(listener2)
BRAIN = PORTS.BRAIN

VISION_5 = PORTS.FIVE

BUTTON_C = PORTS.C
BUTTON_C_PRESSED = SensorHandler(BUTTON_C.pressed)
BUTTON_C_RELEASED = SensorHandler(BUTTON_C.released)

IMU_6 = PORTS.SIX
IMU_6_COLLISION = SensorHandler(PORTS.SIX.collision)

ULTRASONIC_G = PORTS.G

SCREEN_PRESSED = SensorHandler(PORTS.BRAIN.screen.pressed)

LIGHT_ONE = PORTS.B
LIGHT_LEFT = LIGHT_ONE
LIGHT_TWO = PORTS.A
LIGHT_RIGHT = LIGHT_TWO

MOTOR_ONE = PORTS.ONE
MOTOR_LEFT = MOTOR_ONE
MOTOR_TWO = PORTS.TEN
MOTOR_RIGHT = MOTOR_TWO
MOTOR_THREE = PORTS.EIGHT
MOTOR_SCOOP = MOTOR_THREE

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
        self.next = next
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
        BRAIN.screen.set_pen_color(Color.BLACK)
        BRAIN.screen.draw_rectangle(0, 0, 480, 22, Color.BLACK)
        BRAIN.screen.set_pen_color(Color.WHITE)
        BRAIN.screen.print_at(self.to_string() + " -> " + self.next.to_string(), x=0, y=18)
        self.__node.remove()
    def to_string(self):
        return self.name
    def active(self):
        return self.__active
    def set_next(self, next):
        self.next = next


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
    def __init__(self, next = END):
        State.__init__(self, "IDLE", next)
    def enable(self):
        State.enable(self)
        self.listener = BUTTON_C_PRESSED.addEventListener(self.disable, once=True)
    def disable(self):
        State.disable(self)
        self.next.enable()

program_time = 0

class ROBOT_METRICS_STATE(State):
    def __init__(self, next = END):
        State.__init__(self, "BUTTON_DISPLAY", next)
        self.count = 0
        self.handler = None
    def enable(self):
        State.enable(self)
        self.handler = BUTTON_C_PRESSED.addEventListener(self.on_press)
        #vex screen is 480x272 pixels
    def act(self):
        BRAIN.screen.set_pen_color(Color.WHITE)
        BRAIN.screen.draw_rectangle(0, 22, 480, 250, Color.BLACK)
        self.x = 10
        self.y = 42
        BRAIN.screen.set_pen_color(Color.BLUE)
        self.print("Program cycles:")
        self.print(str(program_time))
        self.print("Active States (Est):")
        self.print(str(active_states_estimate))
        self.print("Active States (Act):")
        self.print(str(active_states_actual))
        self.print("Button Presses:")
        self.print(str(self.count))
        self.print("Rotation:")
        self.print(str(IMU_6.rotation()))
        self.print("Distance in front:")
        self.print(str(ULTRASONIC_G.distance(DistanceUnits.CM)))
        self.print("Line sensor left")
        self.print(str(LIGHT_LEFT.value()))
        self.print("Line sensor right")
        self.print(str(LIGHT_RIGHT.value()))
        self.print("fruit close:")
        self.print(len(fruit_close))
        self.print("fruit_far")
        self.print(len(fruit_far))
    def disable(self):
        State.disable(self)
        BUTTON_C_PRESSED.removeEventListener(self.handler)
    def on_press(self):
        self.count = self.count+1
    def print(self, text):
        BRAIN.screen.print_at(text, x = self.x, y = self.y, opaque = False)
        self.y = self.y+20
        if self.y>=240:
            self.y = 42
            self.x = 250

METRICS = ROBOT_METRICS_STATE()
# define the states

class START_STATE(State):
    def __init__(self, next = END):
        State.__init__(self, "START", next)
    def enable(self):
        State.enable(self)
        IMU_6.calibrate()
        BRAIN.screen.set_pen_color(Color.RED)
        BRAIN.screen.print_at("CALIBRATING SENSOR! DON'T MOVE ME!", x=0, y=18)
        while(IMU_6.is_calibrating()):
            sleep(0.2, SECONDS)
        BRAIN.screen.clear_screen()
        BRAIN.screen.set_pen_color(Color.GREEN)
        BRAIN.screen.print_at("Done calibrating, press screen to run :D", x=0, y=18)
        BRAIN.screen.set_pen_color(Color.WHITE)
        SCREEN_PRESSED.addEventListener(self.disable, once = True)
    def disable(self):
        State.disable(self)
        self.next.enable()
        METRICS.enable()
        
class TURN_STATE(State):
    def __init__(self, target_angle, stop_handler: CustomHandler):
        State.__init__(self, "TURN", next = END)
        self.target_angle = target_angle
        self.stop_handler = stop_handler
        self.stop_listener = None
        self.button_listener = None
    def enable(self):
        State.enable(self)
        MOTOR_LEFT.spin(DirectionType.REVERSE)
        MOTOR_RIGHT.spin(DirectionType.FORWARD)
        self.stop_handler.expect()
        self.button_listener = BUTTON_C_PRESSED.addEventListener(self.disable)
        self.stop_listener = self.stop_handler.addEventListener(self.disable)
    def act(self):
        GAIN = 160
        error = self.target_angle - IMU_6.rotation()
        MOTOR_LEFT.set_velocity(GAIN*self.gain_function(error))
        MOTOR_RIGHT.set_velocity(-GAIN*self.gain_function(error))
        PORTS.BRAIN.screen.print_at(str(self.target_angle - IMU_6.rotation()), x=10, y=130)
    def disable(self):
        State.disable(self)
        self.stop_handler.stop_expecting()
        self.stop_handler.removeEventListener(self.stop_listener)
        MOTOR_RIGHT.stop()
        MOTOR_LEFT.stop()
        self.next.enable()
        BUTTON_C_PRESSED.removeEventListener(self.button_listener)
    def gain_function(self, x): #use x/(x+10) so that for large values of degrees velocity isnt insane, but for low values it's also still existent, also use only positive values of x
        sgn = math.copysign(1, x)
        pos = abs(x)
        return sgn*pos/(pos+10)
    
TURN_AFTER_DRIVE = TURN_STATE(180, CustomHandler(lambda: abs(180 - IMU_6.rotation())<0.5))
TURN_AFTER_SECOND_DRIVE = TURN_STATE(0, CustomHandler(lambda: abs(0 - IMU_6.rotation())<0.5))

imu_direction_error = 0

LIGHT_LEFT_ACTIVE = CustomHandler(lambda: LIGHT_LEFT.value() < 2800)
LIGHT_LEFT_DISABLE = CustomHandler(lambda: LIGHT_LEFT.value() > 2850)
pair_handlers(LIGHT_LEFT_ACTIVE, LIGHT_LEFT_DISABLE)
if (LIGHT_LEFT.value()>2900): LIGHT_LEFT_ACTIVE.expect()
else: LIGHT_LEFT_DISABLE.expect()
LIGHT_RIGHT_ACTIVE = CustomHandler(lambda: LIGHT_RIGHT.value() < 2800)
LIGHT_RIGHT_DISABLE = CustomHandler(lambda: LIGHT_RIGHT.value() > 2850)
pair_handlers(LIGHT_RIGHT_ACTIVE, LIGHT_RIGHT_DISABLE)
if (LIGHT_RIGHT.value()>2900): LIGHT_RIGHT_ACTIVE.expect()
else: LIGHT_RIGHT_DISABLE.expect()

class LINE_FOLLOW_CONTROL_STATE(State):
    def __init__(self, next:State = END):
        State.__init__(self, "LINE_FOLLOW_CONTROL", next)
        self.direction = 0
    def enable(self, direction):
        State.enable(self)
        self.direction = direction
    def act(self):
        error = LIGHT_LEFT.value()-LIGHT_RIGHT.value()
        effort = 40*self.gain_function(error)*self.direction
        MOTOR_LEFT.set_velocity(160*self.direction + effort, VelocityUnits.RPM)
        MOTOR_RIGHT.set_velocity(160*self.direction - effort, VelocityUnits.RPM)
    def gain_function(self, x): #use x/(x+10) so that for large values of degrees velocity isnt insane, but for low values it's also still existent, also use only positive values of x
        sgn = math.copysign(1, x)
        pos = abs(x)
        return sgn*pos/(pos+10)

class IMU_PROPORTIONAL_CONTROL_STATE(State):
    def __init__(self, next:State = END):
        State.__init__(self, "IMU_PROPORTIONAL_CONTROL", next)
        self.direction = 0
        self.target_angle = 0
    def enable(self, direction, target_angle):
        State.enable(self)
        self.direction = direction
        self.target_angle = target_angle
    def act(self):
        error = IMU_6.rotation() - self.target_angle
        GAIN = 5.2
        effort = error*GAIN
        MOTOR_LEFT.set_velocity(160*self.direction - effort, VelocityUnits.RPM)
        MOTOR_RIGHT.set_velocity(160*self.direction + effort, VelocityUnits.RPM)

fruit_close = ()
fruit_far = ()

#camera 315 x 211
CAMERA_X = 315
CAMERA_Y = 211
CAMERA_X_DIV_2 = CAMERA_X/2
CAMERA_Y_DIV_2 = CAMERA_Y/2

class FRUITS:
    class ORANGE_FRUIT:
        close = CAMERA_VALUES.ORANGE_FRUIT_CLOSE
        far = CAMERA_VALUES.ORANGE_FRUIT_FAR

    class GREEN_FRUIT: 
        close = CAMERA_VALUES.GREEN_FRUIT_CLOSE
        far = CAMERA_VALUES.GREEN_FRUIT_FAR

    class YELLOW_FRUIT:
        close = CAMERA_VALUES.ORANGE_FRUIT_CLOSE
        far = CAMERA_VALUES.ORANGE_FRUIT_FAR

def fruit_detect_close():
    global fruit_close
    fruit_close = VISION_5.take_snapshot(FRUIT_APPROACH.color.close) or ()
    return len(fruit_close)>0
def fruit_detect_far():
    global fruit_far
    fruit_far = VISION_5.take_snapshot(FRUIT_APPROACH.color.far) or ()
    return len(fruit_far)>0
def fruit_lost_close():
    global fruit_close
    fruit_close = VISION_5.take_snapshot(FRUIT_APPROACH.color.close) or ()
    return len(fruit_close)==0
def fruit_lost_far():
    global fruit_far
    fruit_far = VISION_5.take_snapshot(FRUIT_APPROACH.color.far) or ()
    return len(fruit_far)==0
FRUIT_DETECTED_CLOSE = CustomHandler(fruit_detect_close)
FRUIT_DETECTED_FAR = CustomHandler(fruit_detect_far)
FRUIT_LOST_CLOSE = CustomHandler(fruit_lost_close)
FRUIT_LOST_FAR = CustomHandler(fruit_lost_far)
pair_handlers(FRUIT_DETECTED_CLOSE, FRUIT_LOST_CLOSE)
pair_handlers(FRUIT_DETECTED_FAR, FRUIT_LOST_FAR)


class CAMERA_CONTROL_STATE(State):
    def __init__(self, next:State = END):
        State.__init__(self, "CAMERA_CONTROL", next)
        self.color = None
        self.last_x = 0
        self.last_y = 0
    def enable(self, color):
        State.enable(self)
        self.color = color
        MOTOR_SCOOP.spin(DirectionType.FORWARD)
    def act(self):
        x = 0
        y = 0
        close = fruit_close
        far = fruit_far
        if (len(close)>0):
            x = close[0].centerX - CAMERA_X_DIV_2
            y = close[0].centerY - CAMERA_Y_DIV_2
            self.last_x = x
        elif (len(far)>0):
            x = far[0].centerX - CAMERA_X_DIV_2
            y = far[0].centerY - CAMERA_Y_DIV_2
            self.last_x = x
        else:
            x = self.last_x
        error_x = x
        error_y = y
        effort_x = 40*self.gain_function(error_x)
        effort_y = 10*self.gain_function(error_y)
        MOTOR_LEFT.set_velocity(20-effort_x, VelocityUnits.RPM)
        MOTOR_RIGHT.set_velocity(20+effort_x, VelocityUnits.RPM)
        MOTOR_SCOOP.set_velocity(effort_y, VelocityUnits.RPM)
    def disable(self):
        State.disable(self)
        MOTOR_SCOOP.stop()
    def gain_function(self, error):
        sgn = math.copysign(1, error)
        x = abs(error)
        return sgn/(1+math.exp(-0.1*(x-50))) #logistic curve to have small values at start and major values at end


class FRUIT_SEARCH_STATE(State):
    def __init__(self, next = END):
        State.__init__(self, "FRUIT_SEARCH", next)
    def enable(self):
        MOTOR_LEFT.set_velocity(80, VelocityUnits.RPM)
        MOTOR_RIGHT.set_velocity(-80, VelocityUnits.RPM)


LINE_FOLLOW_CONTROL = LINE_FOLLOW_CONTROL_STATE()
IMU_PROPORTIONAL_CONTROL = IMU_PROPORTIONAL_CONTROL_STATE()
CAMERA_CONTROL = CAMERA_CONTROL_STATE()
FRUIT_SEARCH = FRUIT_SEARCH_STATE()


class DRIVE_STATE(State):
    class Direction:
        FORWARD = 1
        BACKWARD = -1
    def __init__(self, direction, target_angle, stop_handler: CustomHandler):
        State.__init__(self, "DRIVE", next = END)
        self.button_listener = None
        self.stop_handler = stop_handler
        self.stop_listener = None
        self.direction = direction
        self.turned = False
        self.disable_handler = None
        self.target_angle = target_angle
    def enable(self):
        State.enable(self)
        self.button_listener = BUTTON_C_PRESSED.addEventListener(self.disable)
        self.stop_listener = self.stop_handler.addEventListener(self.disable)
        self.stop_handler.expect()
        MOTOR_LEFT.spin(DirectionType.FORWARD)
        self.target_angle = IMU_6.rotation()
        MOTOR_RIGHT.spin(DirectionType.FORWARD)
    def disable(self):
        MOTOR_LEFT.stop()
        MOTOR_RIGHT.stop()
        self.stop_handler.stop_expecting()
        BUTTON_C_PRESSED.removeEventListener(self.button_listener)
        self.stop_handler.removeEventListener(self.stop_listener)
        State.disable(self)
        self.next.enable()

ROBOT_CLOSE = CustomHandler(lambda: ULTRASONIC_G.distance(DistanceUnits.CM)<8)


class HAIL_MARY_DRIVE_STATE(DRIVE_STATE):
    def __init__(self, target_angle_override = None):
        DRIVE_STATE.__init__(self, DRIVE_STATE.Direction.FORWARD, 0, ROBOT_CLOSE)
        self.target_angle_override = target_angle_override
        self.light_left_disable = None
        self.light_right_disable = None
        self.light_left_active = None
        self.light_right_active = None
    def enable(self):
        DRIVE_STATE.enable(self)
        self.light_left_active = LIGHT_LEFT_ACTIVE.addEventListener(self.switch_to_light)
        self.light_right_active = LIGHT_RIGHT_ACTIVE.addEventListener(self.switch_to_light)
        self.light_left_disable = LIGHT_LEFT_DISABLE.addEventListener(self.switch_to_imu)
        self.light_right_disable = LIGHT_RIGHT_DISABLE.addEventListener(self.switch_to_imu)
        if self.target_angle_override!=None: self.target_angle = self.target_angle_override
        if (LIGHT_LEFT.value()>2850 and LIGHT_RIGHT.value()>2850):
            IMU_PROPORTIONAL_CONTROL.enable(self.direction, self.target_angle)
        else:
            LINE_FOLLOW_CONTROL.enable(self.direction)
    def switch_to_imu(self):
        LINE_FOLLOW_CONTROL.disable()
        IMU_PROPORTIONAL_CONTROL.enable(self.direction, self.target_angle)
    def switch_to_light(self):
        IMU_PROPORTIONAL_CONTROL.disable()
        LINE_FOLLOW_CONTROL.enable(self.direction)
    def disable(self):
        LIGHT_LEFT_ACTIVE.removeEventListener(self.light_left_active)
        LIGHT_RIGHT_ACTIVE.removeEventListener(self.light_right_active)
        LIGHT_LEFT_DISABLE.removeEventListener(self.light_left_disable)
        LIGHT_RIGHT_DISABLE.removeEventListener(self.light_right_disable)
        IMU_PROPORTIONAL_CONTROL.disable()
        LINE_FOLLOW_CONTROL.disable()
        DRIVE_STATE.disable(self)

FIRST_DRIVE = HAIL_MARY_DRIVE_STATE(None)
SECOND_DRIVE = HAIL_MARY_DRIVE_STATE(None)

FRUIT_LOST_FAR.addEventListener(lambda: print("Fruit Lost Far"))
FRUIT_LOST_CLOSE.addEventListener(lambda: print("Fruit Lost Close"))


class FRUIT_APPROACH_STATE(DRIVE_STATE):
    def __init__(self):
        DRIVE_STATE.__init__(self, DRIVE_STATE.Direction.FORWARD, 0, ROBOT_CLOSE)
        self.name = "FRUIT_FIND"
        self.fruit_found_close = None
        self.fruit_found_far = None
        self.fruit_lost_close = None
        self.fruit_lost_far = None
        self.lost_cycles = 0
        self.countdown = False
        self.lost_handler = CustomHandler(lambda: self.lost_cycles>20)
        self.lost_event = None
        self.color = FRUITS.GREEN_FRUIT
        self.close = False
        self.far = False
    def enable(self):
        DRIVE_STATE.enable(self)
        MOTOR_LEFT.set_velocity(0)
        MOTOR_RIGHT.set_velocity(0)
        global fruit_far
        fruit_far = VISION_5.take_snapshot(self.color.far) or ()
        global fruit_close
        fruit_close = VISION_5.take_snapshot(self.color.close) or ()
        if (bool(fruit_close)):
            CAMERA_CONTROL.enable(self.color)
            self.close = True
            if bool(fruit_far):
                self.far = True
            else:
                self.far = False
            self.fruit_lost_close = FRUIT_LOST_CLOSE.addEventListener(self.on_fruit_close_lost)
            self.fruit_lost_far = FRUIT_LOST_FAR.addEventListener(self.on_fruit_far_lost)
        elif(bool(fruit_far)):
            CAMERA_CONTROL.enable(self.color)
            self.far = True
            self.close = False
            self.fruit_lost_close = FRUIT_LOST_CLOSE.addEventListener(self.on_fruit_close_lost)
            self.fruit_lost_far = FRUIT_LOST_FAR.addEventListener(self.on_fruit_far_lost)
        else:
            self.far = False
            self.close = False
            FRUIT_SEARCH.enable()
            self.fruit_found_close = FRUIT_DETECTED_CLOSE.addEventListener(self.start_approach)
            self.fruit_found_far = FRUIT_DETECTED_FAR.addEventListener(self.start_approach)
    def act(self):
        self.lost_cycles = self.lost_cycles + 1 #even though this increments when its not lost, it gets reset when it is lost
        if (self.countdown):
            print(self.lost_cycles)
    def start_countdown(self):
        print(str(self.close) + " " + str(self.far) + str(self.countdown))
        if self.close or self.far or self.countdown: return
        self.countdown = True
        self.lost_cycles = 0
        self.lost_handler.expect()
        self.lost_event = self.lost_handler.addEventListener(self.start_searching)
        FRUIT_LOST_CLOSE.removeEventListener(self.fruit_lost_close)
        FRUIT_LOST_FAR.removeEventListener(self.fruit_lost_far)
        self.fruit_found_close = FRUIT_DETECTED_CLOSE.addEventListener(self.remove_countdown)
        self.fruit_found_far = FRUIT_DETECTED_FAR.addEventListener(self.remove_countdown)
    def remove_countdown(self):
        if not self.countdown: return
        self.countdown = False
        self.lost_handler.stop_expecting()
        self.lost_handler.removeEventListener(self.lost_event)
        FRUIT_DETECTED_CLOSE.removeEventListener(self.fruit_found_close)
        FRUIT_DETECTED_FAR.removeEventListener(self.fruit_found_far)
        self.fruit_lost_close = FRUIT_LOST_CLOSE.addEventListener(self.on_fruit_close_lost)
        self.fruit_lost_far = FRUIT_LOST_FAR.addEventListener(self.on_fruit_far_lost)
    def start_searching(self):
        self.countdown = False
        self.lost_handler.stop_expecting()
        self.lost_handler.removeEventListener(self.lost_event)
        FRUIT_DETECTED_CLOSE.removeEventListener(self.fruit_found_close)
        FRUIT_DETECTED_FAR.removeEventListener(self.fruit_found_far)
        FRUIT_SEARCH.enable()
        CAMERA_CONTROL.disable()
        self.fruit_found_close = FRUIT_DETECTED_CLOSE.addEventListener(self.start_approach)
        self.fruit_found_far = FRUIT_DETECTED_FAR.addEventListener(self.start_approach)
    def start_approach(self):
        FRUIT_DETECTED_CLOSE.removeEventListener(self.fruit_found_close)
        FRUIT_DETECTED_FAR.removeEventListener(self.fruit_found_far)
        FRUIT_SEARCH.disable()
        CAMERA_CONTROL.enable(self.color)
        self.fruit_lost_close = FRUIT_LOST_CLOSE.addEventListener(self.on_fruit_close_lost)
        self.fruit_lost_far = FRUIT_LOST_FAR.addEventListener(self.on_fruit_far_lost)
    def disable(self):
        DRIVE_STATE.disable(self)
        CAMERA_CONTROL.disable()
        FRUIT_SEARCH.disable()
        self.lost_handler.removeEventListener(self.lost_event)
        FRUIT_DETECTED_CLOSE.removeEventListener(self.fruit_found_close)
        FRUIT_DETECTED_FAR.removeEventListener(self.fruit_found_far)
        FRUIT_LOST_CLOSE.removeEventListener(self.fruit_lost_close)
        FRUIT_LOST_FAR.removeEventListener(self.fruit_lost_far)
    def on_fruit_close_lost(self):
        self.close = False
        self.start_countdown()
    def on_fruit_far_lost(self):
        self.far = False
        self.start_countdown()
    def on_fruit_close_found(self):
        self.close = True
        self.remove_countdown()
    def on_fruit_far_found(self):
        self.far = True
        self.remove_countdown()
FRUIT_APPROACH = FRUIT_APPROACH_STATE()
        

fruit_close = VISION_5.take_snapshot(FRUIT_APPROACH.color.close) or ()
fruit_far = VISION_5.take_snapshot(FRUIT_APPROACH.color.far) or ()
if (bool(fruit_close)):
    FRUIT_LOST_CLOSE.expect()
else:
    FRUIT_DETECTED_CLOSE.expect()
if (bool(fruit_far)):
    FRUIT_LOST_FAR.expect()
else:
    FRUIT_DETECTED_FAR.expect()

class DRIVE_BACK_STATE(DRIVE_STATE):
    def __init__(self, target_wheel_rotations):
        DRIVE_STATE.__init__(self, DRIVE_STATE.Direction.BACKWARD, 0, CustomHandler(self.target_reached))
        self.name = "DRIVE_BACK"
        self.target_angular_rotation = target_wheel_rotations * 360 * 5
        self.stop_handler.__check_func = self.target_reached
        self.left_initial = MOTOR_LEFT.position()
        self.right_initial = MOTOR_RIGHT.position()
    def enable(self):
        DRIVE_STATE.enable(self)
        IMU_PROPORTIONAL_CONTROL.enable(self.direction, self.target_angle)
        self.left_initial = MOTOR_LEFT.position()
        self.right_initial = MOTOR_RIGHT.position()
    def disable(self):
        IMU_PROPORTIONAL_CONTROL.disable()
        DRIVE_STATE.disable(self)
    def target_reached(self) -> bool:
        return abs(MOTOR_LEFT.position()-self.left_initial)>self.target_angular_rotation and abs(MOTOR_RIGHT.position()-self.right_initial)>self.target_angular_rotation
DRIVE_BACK = DRIVE_BACK_STATE(1)
DRIVE_BACK_AT_END = DRIVE_BACK_STATE(1)

print("Running :)")

IMU_6.set_rotation(0, RotationUnits.DEG)
START = START_STATE()
IDLE = IDLE_STATE()
START.set_next(IDLE)
IDLE.set_next(FRUIT_APPROACH)
FRUIT_APPROACH.set_next(IDLE)
START.enable()


def length():
    count = 0
    head = STATEHEAD
    while (head!=None):
        count = count +1
        head = head.next
    return count

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
    sleep(0.1, SECONDS)

