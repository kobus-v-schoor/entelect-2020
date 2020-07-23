from copy import deepcopy

import pytest

from sloth.enums import Block
from sloth.maps import BlockOverlay, GlobalMap, Map

class TestBlockOverlay:
    def test_init(self):
        block = BlockOverlay(0)
        assert block.block is Block.EMPTY
        block = BlockOverlay(Block.EMPTY)
        assert block.block is Block.EMPTY

    def test_eq(self):
        block1 = BlockOverlay(Block.EMPTY)
        block2 = Block.EMPTY
        assert block1 == block2

        block2 = BlockOverlay(Block.EMPTY)
        assert block1 == block2

        block2 = 0
        with pytest.raises(ValueError):
            block1 == block2

    def test_cybertruck(sself):
        block = BlockOverlay(Block.EMPTY)

        block.set_cybertruck()
        assert block == Block.CYBERTRUCK
        assert block.get_underlay() == Block.EMPTY

class TestGlobalMap:
    def setup_map(self):
        x = 10
        y = 4
        return x, y, GlobalMap(x, y)

    def test_init(self):
        x, y, gmap = self.setup_map()

        assert gmap.min_x == 1
        assert gmap.max_x == x
        assert gmap.min_y == 1
        assert gmap.max_y == y
        assert type(gmap[1, 1]) is BlockOverlay
        assert gmap[1, 1] == Block.EMPTY

    def test_set_and_get(self):
        x, y, gmap = self.setup_map()

        gmap[1, 1] = Block.MUD
        assert gmap[1, 1] == Block.MUD

        gmap[x, y]

        with pytest.raises(IndexError):
            gmap[x + 1, y]
        with pytest.raises(IndexError):
            gmap[x, y + 1]
        with pytest.raises(IndexError):
            gmap[x + 1, y + 1]

class TestMap:
    def setup_gmap(self):
        x = 10
        y = 4
        return x, y, GlobalMap(x, y)

    def test_basic(self):
        x, y, gmap = self.setup_gmap()

        omap = Map(global_map=gmap, raw_map=[
            [{
                'position': {
                    'x': 1,
                    'y': 1,
                },
                'surfaceObject': Block.MUD.value,
                'isOccupiedByCyberTruck': False
            }],
            [{
                'position': {
                    'x': 2,
                    'y': 2,
                },
                'surfaceObject': Block.BOOST.value,
                'isOccupiedByCyberTruck': False
            }]
        ])

        assert omap.min_x == 1
        assert omap.max_x == 2
        assert omap.min_y == 1
        assert omap.max_y == 2

        assert omap[1, 1] == Block.MUD
        assert omap[2, 2] == Block.BOOST
        assert omap[x, y] is gmap[x, y]

    def test_set_get_and_update(self):
        x, y, gmap = self.setup_gmap()
        omap = Map(raw_map=[[]], global_map=gmap)

        omap[1, 1] = Block.MUD
        assert omap[1, 1] == Block.MUD
        assert gmap[1, 1] == Block.EMPTY
        omap.update_global_map()
        assert omap[1, 1] == Block.MUD
        assert gmap[1, 1] == Block.MUD


        omap[x, y]

        with pytest.raises(IndexError):
            omap[x + 1, y]
        with pytest.raises(IndexError):
            omap[x, y + 1]
        with pytest.raises(IndexError):
            omap[x + 1, y + 1]

    def test_deepcopy(self):
        x, y, gmap = self.setup_gmap()
        omap = Map(raw_map=[[]], global_map=gmap)
        omap[1, 1] = Block.MUD

        copy = deepcopy(omap)

        assert copy.view is not omap.view
        assert copy.global_map is omap.global_map

    def test_cybertruck(self):
        x, y, gmap = self.setup_gmap()

        omap = Map(global_map=gmap, raw_map=[
            [{
                'position': {
                    'x': 1,
                    'y': 1,
                },
                'surfaceObject': Block.MUD.value,
                'isOccupiedByCyberTruck': True
            }]
        ])

        assert omap[1, 1] == Block.CYBERTRUCK
        omap[1, 1] = omap[1, 1].get_underlay()
        assert omap[1, 1] == Block.MUD
