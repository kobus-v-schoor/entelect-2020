import copy

from enums import Block

class GlobalMap:
    def __init__(self, x_size, y_size):
        # map dimensions are flipped since generally y << x - this leads to
        # better memory efficiency since we have a few long lists compared to
        # many small lists. will still be x, y in get_item
        self.map = [[Block.EMPTY for _ in range(x_size)] for _ in range(y_size)]
        self.min_x, self.min_y = 1, 1
        self.max_x, self.max_y = x_size, y_size

    # x and y are 1-indexed to be compatible with game format
    def __setitem__(self, idx, val):
        x, y = idx
        if self.min_x <= x <= self.max_x:
            if self.min_y <= y <= self.max_y:
                self.map[y - self.min_y][x - self.min_x] = val
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

            self.min_x = min(x, self.min_x)
            self.min_y = min(y, self.min_y)
            self.max_x = max(x, self.max_x)
            self.max_y = max(y, self.max_y)

        # init mutable view
        self.view = {}

    # write view's changes to global map
    def update_global_map(self):
        for pos in self.view:
            self.global_map[pos] = self.view[pos]
        self.view = {}

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
                self.view[pos] = block
                return
        raise IndexError

    # prevents deep-copying the global map
    def __deepcopy__(self, memo):
        # copies all members (but shallow copies view + global map)
        cm = copy.copy(self)
        # make view a deep copy (but keep the global map shallow)
        cm.view = copy.deepcopy(self.view)

        return cm

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str(vars(self))
