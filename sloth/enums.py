import enum

class Block(enum.Enum):
    EMPTY = 0
    MUD = 1
    OIL_SPILL = 2
    OIL_ITEM = 3
    FINISH_LINE = 4
    BOOST = 5
    WALL = 6
    LIZARD = 7
    TWEET = 8

    CYBERTRUCK = 100

class Speed(enum.Enum):
    MIN_SPEED = 0
    SPEED_1 = 3
    SPEED_2 = 6
    SPEED_3 = 8
    MAX_SPEED = 9

    INIT_SPEED = 5
    BOOST_SPEED = 15

SPEED_STEPS = [
        Speed.MIN_SPEED.value,
        Speed.SPEED_1.value,
        Speed.SPEED_2.value,
        Speed.SPEED_3.value,
        Speed.MAX_SPEED.value,
        ]

def next_speed(speed):
    try:
        return next(s for s in SPEED_STEPS if s > speed)
    except StopIteration:
        return SPEED_STEPS[-1]

def prev_speed(speed):
    try:
        return next(s for s in SPEED_STEPS[::-1] if s < speed)
    except StopIteration:
        return SPEED_STEPS[0]

class Cmd:
    class CmdEnum(enum.Enum):
        NOP = 'NOTHING'

        ACCEL = 'ACCELERATE'
        DECEL = 'DECELERATE'
        LEFT = 'TURN_LEFT'
        RIGHT = 'TURN_RIGHT'

        BOOST = 'USE_BOOST'
        OIL = 'USE_OIL'
        LIZARD = 'USE_LIZARD'
        TWEET = 'USE_TWEET'

    def __init__(self, cmd):
        if type(cmd) is Cmd.CmdEnum:
            self.cmd = cmd
        elif type(val) is Cmd:
            self.cmd = cmd.cmd
        else:
            self.cmd = CmdEnum(cmd)

    def __eq__(self, other):
        if type(other) is Cmd.CmdEnum:
            return self.cmd == other
        elif type(other) is Cmd:
            return self.cmd == other.cmd
        raise ValueError(f'unsupported type {type(other)} for operand ==')

    def __hash__(self):
        return hash(self.cmd)

    def __repr__(self):
        return repr(self.cmd)

    def __str__(self):
        return self.cmd.value

for cmd in Cmd.CmdEnum:
    setattr(Cmd, cmd.name, cmd)
