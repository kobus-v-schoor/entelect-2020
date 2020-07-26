import copy

from sloth.enums import Block

class BlockOverlay:
    def __init__(self, block):
        if type(block) is Block:
            self.block = block
            self.overlay = None
        elif type(block) is BlockOverlay:
            self.block = block.block
            self.overlay = block.overlay
        else:
            self.block = Block(block)
            self.overlay = None

    def bad_block(self):
        return self.get_block() in [Block.MUD, Block.WALL, Block.OIL_SPILL,
                                    Block.CYBERTRUCK]

    def set_cybertruck(self):
        self.overlay = Block.CYBERTRUCK

    def get_block(self):
        if self.overlay is not None:
            return self.overlay
        return self.block

    def get_underlay(self):
        return self.block

    def __hash__(self):
        return hash(self.get_block())

    def __eq__(self, other):
        if type(other) is Block:
            return self.get_block() == other
        elif type(other) is BlockOverlay:
            return self.get_block() == other.get_block()
        raise ValueError(f'unsupported type {type(other)} for operand ==')

    def __repr__(self):
        gb = self.get_block()
        if gb != self.block:
            return f'{repr(gb)} ({repr(self.block)})'
        else:
            return repr(gb)

    def __str__(self):
        return repr(self)

class GlobalMap:
    def __init__(self, x_size, y_size):
        # map dimensions are flipped since generally y << x - this leads to
        # better memory efficiency since we have a few long lists compared to
        # many small lists. will still be x, y in get_item
        self.map = [[BlockOverlay(Block.EMPTY) for _ in range(x_size)] for _ in
                    range(y_size)]
        self.min_x, self.min_y = 1, 1
        self.max_x, self.max_y = x_size, y_size

    # x and y are 1-indexed to be compatible with game format
    def __setitem__(self, idx, val):
        x, y = idx
        if self.min_x <= x <= self.max_x:
            if self.min_y <= y <= self.max_y:
                self.map[y - self.min_y][x - self.min_x] = BlockOverlay(val)
                return
        raise IndexError

    # x and y are 1-indexed to be compatible with game format
    def __getitem__(self, idx):
        x, y = idx
        if self.min_x <= x <= self.max_x:
            if self.min_y <= y <= self.max_y:
                return self.map[y - self.min_y][x - self.min_x]
        raise IndexError

class Map:
    def __init__(self, raw_map, global_map):
        # store global map
        self.global_map = global_map

        # init mutable view
        self.view = {}

        # flatten raw_map dict
        raw_map = [w for row in raw_map for w in row]

        # init min and max bounds
        self.min_x = float('inf')
        self.min_y = float('inf')
        self.max_x = float('-inf')
        self.max_y = float('-inf')

        # parse map and update global map
        for w in raw_map:
            x = w['position']['x']
            y = w['position']['y']
            global_map[x, y] = Block(w['surfaceObject'])

            if w.get('isOccupiedByCyberTruck', False):
                global_map[x, y].set_cybertruck()

            self.min_x = min(x, self.min_x)
            self.min_y = min(y, self.min_y)
            self.max_x = max(x, self.max_x)
            self.max_y = max(y, self.max_y)

    # write view's changes to global map
    def update_global_map(self):
        for pos in self.view:
            self.global_map[pos] = self.view[pos]
        self.view = {}

    # moves the min and max x bounds relative to two x positions
    def move_window(self, from_x, to_x):
        self.min_x = max(self.global_map.min_x, self.min_x + to_x - from_x)
        self.max_x = min(self.global_map.max_x, self.max_x + to_x - from_x)

    def __getitem__(self, pos):
        x, y = pos

        if self.global_map.min_x <= x <= self.global_map.max_x:
            if self.global_map.min_y <= y <= self.global_map.max_y:
                return self.view.get(pos, self.global_map[x, y])
        raise IndexError

    # only makes changes to the mutable view, not the global map. use
    # update_global_map to propogate changes.
    def __setitem__(self, pos, block):
        x, y = pos

        if self.global_map.min_x <= x <= self.global_map.max_x:
            if self.global_map.min_y <= y <= self.global_map.max_y:
                self.view[pos] = BlockOverlay(block)
                return
        raise IndexError

    # prevents deep-copying the global map
    def __deepcopy__(self, memo):
        # copies all members (but shallow copies view + global map)
        cm = copy.copy(self)
        # make view a deep copy (but keep the global map shallow)
        cm.view = copy.deepcopy(self.view)

        return cm

    def __hash__(self):
        return hash(tuple([(*pos, self.view[pos]) for pos in
                           sorted(self.view)]))

    def __eq__(self, other):
        return self.view == other.view

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str(vars(self))

# removes all temporary terrain in front of opponent
def clean_map(state, from_x, to_x):
    for y in range(state.map.min_y, state.map.max_y + 1):
        for x in range(from_x, to_x + 1):
            block = state.map.global_map[x, y]

            # remove any blocks that wasn't here when to opponent was here
            if block == Block.OIL_SPILL:
                # just a guess, we can't do any better
                state.map[x, y] = Block.EMPTY
            elif block == Block.CYBERTRUCK:
                state.map[x, y] = block.get_underlay()
