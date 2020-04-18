class Player:
    def __init__(self, raw_player):
        # position and speed
        self.x = raw_player['position']['x']
        self.y = raw_player['position']['y']
        self.speed = raw_player['speed']

        # powerup info if available
        if 'powerups' in raw_player:
            powerups = raw_player['powerups']
            self.boosts = len([b for b in powerups if b == 'BOOST'])
            self.oils = len([o for o in powerups if o == 'OIL'])

            self.boosting = raw_player['boosting']
            self.boost_counter = raw_player['boostCounter']
        else:
            self.boosts = 0
            self.oils = 0
            self.boosting = False
            self.boost_counter = 0

    def __hash__(self):
        return hash(vars(self).items())

    def __eq__(self, other):
        return vars(self) == vars(other)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str(vars(self))

class State:
    def __init__(self):
        self.map = None
        self.player = None
        self.opp = None

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str({'player': self.player, 'opp': self.opp})

    # extract a tuple that can be used to describe a unique state. used for
    # hashing and equality checks
    # used to exclude vars that should not be included in comparison
    def xvars(self):
        return (self.player, self.opp)

    def __hash__(self):
        return hash(self.xvars())

    def __eq__(self, other):
        return self.xvars() == other.xvars() if type(other) is State else False
