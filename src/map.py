from enums import Block

class GlobalMap:
    def __init__(self, x_size, y_size):
        # map dimensions are flipped since generally y << x - this leads to
        # better memory efficiency since we have a few long lists compared to
        # many small lists. will still be x, y in get_item
        self.map = [[Block.EMPTY for _ in range(x_size)] for _ in range(y_size)]

    # x and y are 1-indexed to be compatible with game format
    def __setitem__(self, idx, val):
        x, y = idx
        self.map[y-1][x-1] = val

    # x and y are 1-indexed to be compatible with game format
    def __getitem__(self, idx):
        x, y = idx
        return self.map[y-1][x-1]

class Map:
    def __init__(self, x, y, world_map):
        # flatten map
        world_map = [w for row in world_map for w in row]

        # find bounds
        min_x = min(world_map, key=lambda w:w['position']['x'])['position']['x']
        max_x = max(world_map, key=lambda w:w['position']['x'])['position']['x']
        min_y = min(world_map, key=lambda w:w['position']['y'])['position']['y']
        max_y = max(world_map, key=lambda w:w['position']['y'])['position']['y']

        # store absolute minimum and maximum values
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

        # generate map
        rows = max_y - min_y + 1
        cols = max_x - min_x + 1

        # order: map[x][y]
        self.map = [[Block.EMPTY for _ in range(rows)] for _ in range(cols)]

        # fill in map
        for w in world_map:
            mx = w['position']['x']
            my = w['position']['y']
            self.map[mx - min_x][my - min_y] = Block(w['surfaceObject'])

        self.update_xy(x, y)

    def update_xy(self, x, y):
        # player position
        self.x = x
        self.y = y

        # these are relative, meaning that if rel_min_y == 0 then you cannot
        # move further to the right - same goes for rel_max_y, if rel_max_y == 0
        # you cannot go further to the left
        self.rel_min_x = self.min_x - x
        self.rel_max_x = self.max_x - x
        self.rel_min_y = self.min_y - y
        self.rel_max_y = self.max_y - y

    # updates a given GlobalMap with the values in this map
    def update_global_map(self, global_map):
        for x, col in enumerate(self.map):
            for y, val in enumerate(col):
                global_map[self.min_x + x, self.min_y + y] = val

    # returns the map item relative to the current position with order [x,y]
    # this means that [0, 0] returns the current block, [1,-1] returns one block
    # to the right and one block back
    # use rel_min and rel_max variables for bounds
    def __getitem__(self, key):
        x, y = key

        if self.rel_min_x <= x <= self.rel_max_x:
            if self.rel_min_y <= y <= self.rel_max_y:
                return self.map[x - self.rel_min_x][y - self.rel_min_y]
        raise IndexError

    def __setitem__(self, key, val):
        x, y = key

        if self.rel_min_x <= x <= self.rel_max_x:
            if self.rel_min_y <= y <= self.rel_max_y:
                self.map[x - self.rel_min_x][y - self.rel_min_y] = val
                return
        raise IndexError
