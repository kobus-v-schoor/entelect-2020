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
    EMP = 9

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

MAX_SPEED_STEPS = [
    Speed.BOOST_SPEED.value,
    Speed.MAX_SPEED.value,
    Speed.SPEED_3.value,
    Speed.SPEED_2.value,
    Speed.SPEED_1.value,
    Speed.MIN_SPEED.value,
]

def max_speed(damage):
    return MAX_SPEED_STEPS[max(1, min(damage, 5))]

def boost_speed(damage):
    return MAX_SPEED_STEPS[max(0, min(damage, 5))]

def next_speed(speed, damage=0):
    m = max_speed(damage)
    try:
        return next(s for s in SPEED_STEPS if s > speed and s <= m)
    except StopIteration:
        return m

def prev_speed(speed, damage=0):
    m = max_speed(damage)
    try:
        return next(s for s in SPEED_STEPS[::-1] if s < speed and s <= m)
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
        EMP = 'USE_EMP'
        FIX = 'FIX'

    def __init__(self, cmd, pos=None):
        if type(cmd) is Cmd.CmdEnum:
            self.cmd = cmd
        elif type(cmd) is Cmd:
            self.cmd = cmd.cmd
        else:
            self.cmd = Cmd.CmdEnum(cmd)

        self.pos = pos

    def __eq__(self, other):
        if type(other) is Cmd.CmdEnum:
            return self.cmd == other
        elif type(other) is Cmd:
            return (self.cmd, self.pos) == (other.cmd, other.pos)
        raise ValueError(f'unsupported type {type(other)} for operand ==')

    def __hash__(self):
        return hash((self.cmd, self.pos))

    def __repr__(self):
        if self.pos is None:
            return repr(self.cmd)
        else:
            return repr((self.cmd, self.pos))

    def __str__(self):
        if self.pos is None:
            return str(self.cmd.value)
        else:
            return f'{self.cmd.value} {self.pos[1]} {self.pos[0]}'

for cmd in Cmd.CmdEnum:
    setattr(Cmd, cmd.name, cmd)
