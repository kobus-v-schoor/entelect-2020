import enum

class Block(enum.Enum):
    EMPTY = 0
    MUD = 1
    OIL_SPILL = 2
    OIL_ITEM = 3
    FINISH_LINE = 4
    BOOST = 5

class Speed(enum.Enum):
    MIN_SPEED = 0
    SPEED_1 = 1
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

class Cmd(enum.Enum):
    NOP = 'NOTHING'

    ACCEL = 'ACCELERATE'
    DECEL = 'DECELERATE'
    LEFT = 'TURN_LEFT'
    RIGHT = 'TURN_RIGHT'

    BOOST = 'USE_BOOST'
    OIL = 'USE_OIL'

CMD_SEARCH = [
        Cmd.NOP,
        Cmd.ACCEL,
        # Cmd.DECEL, # never used, taken out to improve performance
        Cmd.LEFT,
        Cmd.RIGHT,
        Cmd.BOOST,
        # Cmd.OIL, # only used when doing nothing else
        ]
