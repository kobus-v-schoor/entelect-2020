from sloth.state import Player, State, valid_actions, next_state, calc_opp_cmd
from sloth.maps import GlobalMap, Map
from sloth.enums import Block, Speed, Cmd, prev_speed, next_speed, max_speed

class TestPlayer:
    def setup_player(self):
        return Player({
            'id': 1,
            'position': {
                'x': 2,
                'y': 3,
            },
            'speed': 5
        })

    def test_init(self):
        p = Player({
            'id': 1,
            'position': {
                'x': 2,
                'y': 3,
            },
            'speed': 5,
            'powerups': [
                'BOOST',
                'OIL',
                'OIL',
                'LIZARD',
                'LIZARD',
                'LIZARD',
                'TWEET',
                'TWEET',
                'TWEET',
                'TWEET',
                'EMP',
                'EMP',
                'EMP',
                'EMP',
                'EMP',
            ],
            'boosting': True,
            'boostCounter': 3,
            'damage': 4,
            'score': 100
        })

        assert p.id == 1
        assert p.x == 2
        assert p.y == 3
        assert p.speed == 5
        assert p.boosts == 1
        assert p.oils == 2
        assert p.lizards == 3
        assert p.tweets == 4
        assert p.emps == 5
        assert p.boosting == True
        assert p.boost_counter == 3
        assert p.damage == 4
        assert p.score == 100

    def test_transfer_mods(self):
        player1 = self.setup_player()
        player2 = self.setup_player()

        player1.boosts = 1
        player1.oils = 2
        player1.lizards = 3
        player1.tweets = 4
        player1.emps = 5

        player1.boosting = True
        player1.boost_counter = 3

        player1.damage = 3
        player1.score = 110

        player1.transfer_mods(player2)

        assert player2.boosts == 1
        assert player2.oils == 2
        assert player2.lizards == 3
        assert player2.tweets == 4
        assert player2.emps == 5

        assert player2.boosting == True
        assert player2.boost_counter == 3

        assert player2.damage == 3
        assert player2.score == 110

    def test_hash_eq(self):
        player1 = self.setup_player()
        player2 = self.setup_player()

        assert player1 is not player2
        assert hash(player1) == hash(player2)
        assert player1 == player2

class TestState:
    def test_switch(self):
        player = Player({
            'id': 1,
            'position': {
                'x': 1,
                'y': 1,
            },
            'speed': 5
        })

        opponent = Player({
            'id': 2,
            'position': {
                'x': 1,
                'y': 4,
            },
            'speed': 5
        })

        class TmpMap:
            def __init__(self):
                self.called = False
            def move_window(self, *args):
                self.called = True

        state = State()
        state.player = player
        state.opponent = opponent
        state.map = TmpMap()

        switch = state.switch()

        assert switch is not state
        assert switch.player == state.opponent
        assert switch.opponent == state.player
        assert switch.map.called == True

def setup_state():
    player = Player({
        'id': 1,
        'position': {
            'x': 1,
            'y': 1,
        },
        'speed': Speed.SPEED_3.value
    })

    opponent = Player({
        'id': 2,
        'position': {
            'x': 1,
            'y': 4,
        },
        'speed': Speed.SPEED_3.value
    })

    global_map = GlobalMap(1500, 4)
    raw_map = [[{
        'position': {
            'x': x,
            'y': y,
        },
        'surfaceObject': Block.EMPTY.value,
        'isOccupiedByCyberTruck': False,
    } for x in range(1, 22)] for y in range(1, 5)]
    track_map = Map(raw_map, global_map)

    state = State()
    state.map = track_map
    state.player = player
    state.opponent = opponent

    return state

class TestValidActions:
    def test_nop(self):
        state = setup_state()
        assert Cmd.NOP in valid_actions(state)

    def test_accel(self):
        state = setup_state()
        assert Cmd.ACCEL in valid_actions(state)
        state.player.speed = Speed.MAX_SPEED.value
        assert Cmd.ACCEL not in valid_actions(state)

        state.player.damage = 2
        state.player.speed = max_speed(state.player.damage)
        assert Cmd.ACCEL not in valid_actions(state)

    def test_left(self):
        state = setup_state()
        assert Cmd.LEFT not in valid_actions(state)
        state.player.y = 2
        assert Cmd.LEFT in valid_actions(state)

    def test_right(self):
        state = setup_state()
        assert Cmd.RIGHT in valid_actions(state)
        state.player.y = 4
        assert Cmd.RIGHT not in valid_actions(state)

    def test_boosts(self):
        state = setup_state()
        assert Cmd.BOOST not in valid_actions(state)
        state.player.boosts = 1
        assert Cmd.BOOST in valid_actions(state)
        state.player.boosting = True
        assert Cmd.BOOST not in valid_actions(state)

    def test_lizards(self):
        state = setup_state()
        assert Cmd.LIZARD not in valid_actions(state)
        state.player.lizards = 1
        assert Cmd.LIZARD in valid_actions(state)

    # add back when next state accepts offensive actions
    # def test_emp(self):
    #     state = setup_state()
    #     assert Cmd.EMP not in valid_actions(state)
    #     state.player.emps = 1
    #     assert Cmd.EMP in valid_actions(state)

    def test_fix(self):
        state = setup_state()
        assert Cmd.FIX not in valid_actions(state)
        state.player.damage = 1
        assert Cmd.FIX in valid_actions(state)

class TestNextState:
    def test_nop(self):
        state = setup_state()
        cmd = Cmd.NOP

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev.speed

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = Block.MUD

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev_speed(prev.speed)

    def test_accel(self):
        state = setup_state()
        cmd = Cmd.ACCEL

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == next_speed(prev.speed)
            assert cur.speed == next_speed(prev.speed)

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = Block.MUD

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == next_speed(prev.speed)
            assert cur.speed == prev.speed

    def test_decel(self):
        state = setup_state()
        cmd = Cmd.DECEL

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev_speed(prev.speed)
            assert cur.speed == prev_speed(prev.speed)

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = Block.MUD

        nstate = next_state(state, Cmd.DECEL, Cmd.DECEL)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev_speed(prev.speed)
            assert cur.speed == prev_speed(prev_speed(prev.speed))

    def test_left(self):
        state = setup_state()
        state.player.y = 2
        cmd = Cmd.LEFT

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y - 1
            assert cur.x - prev.x == prev.speed - 1
            assert cur.speed == prev.speed

        for player in [state.player, state.opponent]:
            state.map[player.x, player.y - 1] = Block.MUD

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y - 1
            assert cur.x - prev.x == prev.speed - 1
            assert cur.speed == prev_speed(prev.speed)

    def test_right(self):
        state = setup_state()
        state.opponent.y = 3
        cmd = Cmd.RIGHT

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y + 1
            assert cur.x - prev.x == prev.speed - 1
            assert cur.speed == prev.speed

        for player in [state.player, state.opponent]:
            state.map[player.x, player.y + 1] = Block.MUD

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y + 1
            assert cur.x - prev.x == prev.speed - 1
            assert cur.speed == prev_speed(prev.speed)

    def test_boost(self):
        state = setup_state()
        state.player.boosts = 1
        state.opponent.boosts = 1
        cmd = Cmd.BOOST

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == Speed.BOOST_SPEED.value
            assert cur.speed == Speed.BOOST_SPEED.value
            assert cur.boosts - prev.boosts == -1
            assert cur.boosting == True
            assert cur.boost_counter == 5

        for i in range(5):
            pstate = nstate
            nstate = next_state(nstate, Cmd.NOP, cmd.NOP)
            for prev, cur in zip([pstate.player, pstate.opponent],
                                 [nstate.player, nstate.opponent]):
                assert cur.boost_counter - prev.boost_counter == -1
                if i < 4:
                    assert cur.boosting == True
                    assert cur.speed == Speed.BOOST_SPEED.value
                else:
                    assert cur.boosting == False
                    assert cur.speed == Speed.MAX_SPEED.value

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = Block.MUD

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == Speed.BOOST_SPEED.value
            assert cur.speed == Speed.MAX_SPEED.value
            assert cur.boosts - prev.boosts == -1
            assert cur.boosting == False

    def test_lizard(self):
        state = setup_state()
        state.player.lizards = 1
        state.opponent.lizards = 1
        cmd = Cmd.LIZARD

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev.speed

        for player in [state.player, state.opponent]:
            for x in range(1, player.speed):
                state.map[player.x + x, player.y] = Block.MUD

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev.speed

        for player in [state.player, state.opponent]:
            state.map[player.x + player.speed, player.y] = Block.MUD

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev_speed(prev.speed)

    def test_fix(self):
        state = setup_state()
        state.player.damage = 3
        state.opponent.damage = 3
        cmd = Cmd.FIX

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x == prev.x
            assert cur.speed == prev.speed
            assert prev.damage == 3
            assert cur.damage == 1

        state.player.damage = 1
        state.opponent.damage = 1

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x == prev.x
            assert cur.speed == prev.speed
            assert prev.damage == 1
            assert cur.damage == 0

        state.player.damage = 0
        state.opponent.damage = 0

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x == prev.x
            assert cur.speed == prev.speed
            assert prev.damage == 0
            assert cur.damage == 0

    def test_hit_mud(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.MUD

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev_speed(prev.speed)
            assert cur.score - prev.score == -3
            assert nstate.map[prev.x + 1, prev.y] == block
            assert prev.damage == 0
            assert cur.damage == 1

    def test_hit_oil_spill(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.OIL_SPILL

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev_speed(prev.speed)
            assert cur.score - prev.score == -4
            assert nstate.map[prev.x + 1, prev.y] == block
            assert prev.damage == 0
            assert cur.damage == 1

    def test_hit_oil_item(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.OIL_ITEM

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev.speed
            assert cur.oils - prev.oils == 1
            assert cur.score - prev.score == 4
            assert nstate.map[prev.x + 1, prev.y] == block
            assert prev.damage == 0
            assert cur.damage == 0

    def test_hit_boost(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.BOOST

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev.speed
            assert cur.boosts - prev.boosts == 1
            assert cur.score - prev.score == 4
            assert nstate.map[prev.x + 1, prev.y] == block
            assert prev.damage == 0
            assert cur.damage == 0

    def test_hit_wall(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.WALL

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == Speed.SPEED_1.value
            assert cur.score - prev.score == -5
            assert nstate.map[prev.x + 1, prev.y] == block
            assert prev.damage == 0
            assert cur.damage == 2

    def test_hit_lizard(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.LIZARD

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev.speed
            assert cur.lizards - prev.lizards == 1
            assert cur.score - prev.score == 4
            assert nstate.map[prev.x + 1, prev.y] == block
            assert prev.damage == 0
            assert cur.damage == 0

    def test_hit_tweet(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.TWEET

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev.speed
            assert cur.tweets - prev.tweets == 1
            assert cur.score - prev.score == 4
            assert nstate.map[prev.x + 1, prev.y] == block
            assert prev.damage == 0
            assert cur.damage == 0

    def test_hit_emp(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.EMP

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x - prev.x == prev.speed
            assert cur.speed == prev.speed
            assert cur.emps - prev.emps == 1
            assert cur.score - prev.score == 4
            assert nstate.map[prev.x + 1, prev.y] == block
            assert prev.damage == 0
            assert cur.damage == 0

    def test_hit_cybertruck(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.EMPTY

        for player in [state.player, state.opponent]:
            state.map[player.x + 2, player.y] = block
            state.map[player.x + 2, player.y].set_cybertruck()
            assert player.speed > 1

        # TODO fix multi hit cybertruck bug
        # state.map.update_global_map() # this triggers it because previously
        # an overlay was created for the state, maybe use that to fix it? in
        # map creation rather don't write cybertruck to global map? idk

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x == prev.x + 1
            assert cur.speed == Speed.SPEED_1.value
            assert cur.score - prev.score == -7
            assert nstate.map[prev.x + 2, prev.y] == block
            assert state.map[prev.x + 2, prev.y] == Block.CYBERTRUCK
            assert prev.damage == 0
            assert cur.damage == 2

    def test_hit_cybertruck_both_samelane(self):
        state = setup_state()

        state.player.x = 1
        state.player.y = 1
        state.player.speed = 9

        state.opponent.x = 2
        state.opponent.y = 1
        state.opponent.speed = 6

        state.map[5, 1].set_cybertruck()

        nstate = next_state(state, Cmd.NOP, Cmd.NOP)

        assert nstate.player.y == state.opponent.y == 1
        assert nstate.opponent.x == 4 # one behind cybertruck
        assert nstate.opponent.speed == Speed.SPEED_1.value
        assert nstate.player.x == 3 # one behind opponent (rear-end)
        assert nstate.player.speed == Speed.SPEED_1.value
        assert nstate.map[5, 1] == Block.EMPTY
        assert nstate.player.damage == 2
        assert nstate.opponent.damage == 2

    def test_hit_cybertruck_both_difflane(self):
        state = setup_state()

        state.player.x = 1
        state.player.y = 1
        state.player.speed = 9

        state.opponent.x = 1
        state.opponent.y = 3
        state.opponent.speed = 6

        state.map[3, 2].set_cybertruck()

        nstate = next_state(state, Cmd.RIGHT, Cmd.LEFT)

        # both end up right behind the cybertruck, where they collide and move
        # back -1x into their original lanes
        assert nstate.player.x == 1
        assert nstate.player.y == 1
        assert nstate.player.speed == Speed.SPEED_1.value

        assert nstate.opponent.x == 1
        assert nstate.opponent.y == 3
        assert nstate.opponent.speed == Speed.SPEED_1.value

        assert nstate.player.damage == 2
        assert nstate.opponent.damage == 2

        assert nstate.map[3, 2] == Block.EMPTY

    def test_collision_same_block(self):
        state = setup_state()
        state.player.x = 1
        state.player.y = 2
        state.opponent.x = 1
        state.opponent.y = 4

        nstate = next_state(state, Cmd.RIGHT, Cmd.LEFT)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert cur.y == prev.y
            assert cur.x == prev.x + prev.speed - 2
            assert cur.speed == prev.speed
            assert cur.score == prev.score
            assert prev.damage == 0
            assert cur.damage == 0

    def test_collision_rear_end(self):
        state = setup_state()

        state.player.speed = Speed.SPEED_1.value
        state.opponent.speed = Speed.SPEED_1.value

        state.player.x = 2
        state.player.y = 2
        state.opponent.x = 1
        state.opponent.y = 2

        nstate = next_state(state, Cmd.NOP, Cmd.ACCEL)

        assert nstate.player.x == state.player.x + state.player.speed
        assert nstate.player.y == state.player.y
        assert nstate.opponent.x == nstate.player.x - 1
        assert nstate.opponent.y == state.opponent.y
        assert nstate.player.damage == 0
        assert nstate.opponent.damage == 0

        state.player.x = 1
        state.player.y = 2
        state.opponent.x = 2
        state.opponent.y = 2

        nstate = next_state(state, Cmd.ACCEL, Cmd.NOP)

        assert nstate.player.x == nstate.opponent.x - 1
        assert nstate.player.y == state.player.y
        assert nstate.opponent.x == state.opponent.x + state.opponent.speed
        assert nstate.opponent.y == state.opponent.y
        assert nstate.player.damage == 0
        assert nstate.opponent.damage == 0

    def test_collision_rear_end_same_block(self):
        state = setup_state()

        state.player.speed = 8
        state.opponent.speed = 9

        state.player.x = 2
        state.player.y = 2
        state.opponent.x = 1
        state.opponent.y = 2

        nstate = next_state(state, Cmd.NOP, Cmd.NOP)

        assert (state.player.x + state.player.speed ==
                state.opponent.x + state.opponent.speed)
        assert nstate.player.x == state.player.x + state.player.speed
        assert nstate.player.y == state.player.y
        assert nstate.opponent.x == nstate.player.x - 1
        assert nstate.opponent.y == state.opponent.y
        assert nstate.player.damage == 0
        assert nstate.opponent.damage == 0

        state.player.speed = 9
        state.opponent.speed = 8

        state.player.x = 1
        state.player.y = 2
        state.opponent.x = 2
        state.opponent.y = 2

        nstate = next_state(state, Cmd.NOP, Cmd.NOP)

        assert (state.player.x + state.player.speed ==
                state.opponent.x + state.opponent.speed)
        assert nstate.player.x == nstate.opponent.x - 1
        assert nstate.player.y == state.player.y
        assert nstate.opponent.x == state.opponent.x + state.opponent.speed
        assert nstate.opponent.y == state.opponent.y
        assert nstate.player.damage == 0
        assert nstate.opponent.damage == 0

    def test_collision_lizarding(self):
        state = setup_state()

        state.player.x = 2
        state.player.y = 2
        state.player.speed = Speed.SPEED_1.value
        state.opponent.x = 1
        state.opponent.y = 2
        state.opponent.speed = Speed.MAX_SPEED.value

        nstate = next_state(state, Cmd.NOP, Cmd.LIZARD)

        assert state.player.x > state.opponent.x
        assert nstate.player.x == state.player.x + state.player.speed
        assert nstate.player.y == state.player.y
        assert nstate.opponent.x == state.opponent.x + state.opponent.speed
        assert nstate.opponent.y == state.opponent.y
        assert nstate.opponent.x > nstate.player.x
        assert nstate.player.damage == 0
        assert nstate.opponent.damage == 0

        state.player.x = 1
        state.player.y = 2
        state.player.speed = Speed.MAX_SPEED.value
        state.opponent.x = 2
        state.opponent.y = 2
        state.opponent.speed = Speed.SPEED_1.value

        nstate = next_state(state, Cmd.LIZARD, Cmd.NOP)

        assert state.opponent.x > state.player.x
        assert nstate.player.x == state.player.x + state.player.speed
        assert nstate.player.y == state.player.y
        assert nstate.opponent.x == state.opponent.x + state.opponent.speed
        assert nstate.opponent.y == state.opponent.y
        assert nstate.player.x > nstate.opponent.x
        assert nstate.player.damage == 0
        assert nstate.opponent.damage == 0

    def test_damage_cap(self):
        state = setup_state()
        cmd = Cmd.NOP
        block = Block.WALL

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block
            player.damage = 4

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert prev.damage == 4
            assert cur.damage == 6

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block
            player.damage = 5

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert prev.damage == 5
            assert cur.damage == 6

        for player in [state.player, state.opponent]:
            state.map[player.x + 1, player.y] = block
            player.damage = 6

        nstate = next_state(state, cmd, cmd)
        for prev, cur in zip([state.player, state.opponent],
                             [nstate.player, nstate.opponent]):
            assert prev.damage == 6
            assert cur.damage == 6

    def test_damage_speed_limit(self):
        state = setup_state()
        cmd = Cmd.ACCEL

        # normal, no damage
        state.player.speed = Speed.SPEED_3.value
        state.opponent.speed = Speed.SPEED_3.value

        nstate = next_state(state, cmd, cmd)
        assert nstate.player.speed == Speed.MAX_SPEED.value
        assert nstate.opponent.speed == Speed.MAX_SPEED.value

        # speed capped at SPEED_3, so should do nothing
        state.player.damage = 1
        state.opponent.damage = 1

        nstate = next_state(state, cmd, cmd)
        assert nstate.player.speed == Speed.SPEED_3.value
        assert nstate.opponent.speed == Speed.SPEED_3.value

        # should be able to accel to SPEED_3
        state.player.speed = Speed.SPEED_2.value
        state.opponent.speed = Speed.SPEED_2.value

        nstate = next_state(state, cmd, cmd)
        assert nstate.player.speed == Speed.SPEED_3.value
        assert nstate.opponent.speed == Speed.SPEED_3.value

        # speed capped at SPEED_2
        state.player.damage = 2
        state.opponent.damage = 2
        state.player.speed = Speed.SPEED_1.value
        state.opponent.speed = Speed.SPEED_1.value

        nstate = next_state(state, cmd, cmd)
        assert nstate.player.speed == Speed.SPEED_2.value
        assert nstate.opponent.speed == Speed.SPEED_2.value

        # speed capped at MIN_SPEED (0)
        # not testing boost because it might have different logic
        state.player.lizards = 1
        state.opponent.lizards = 1

        for cmd in [Cmd.ACCEL, Cmd.LEFT, Cmd.RIGHT, Cmd.DECEL, Cmd.NOP,
                    Cmd.LIZARD]:
            state.player.damage = 6
            state.opponent.damage = 6
            state.player.speed = Speed.MIN_SPEED.value
            state.opponent.speed = Speed.MIN_SPEED.value

            nstate = next_state(state, cmd, cmd)
            assert nstate.player.speed == Speed.MIN_SPEED.value
            assert nstate.opponent.speed == Speed.MIN_SPEED.value
            assert nstate.player.x == state.player.x
            assert nstate.player.y == state.player.y
            assert nstate.opponent.x == state.opponent.x
            assert nstate.opponent.y == state.opponent.y

    def test_damage_boost_limit(self):
        # TODO implement this when rules are clarified
        pass

class TestCalcOppCmd:
    def test_valid_cmds(self):
        state = setup_state()
        state.opponent.y = 3
        state.opponent.boosts = 1
        state.opponent.lizards = 1
        state.map[2, 3] = Block.MUD

        for action in valid_actions(state.switch()):
            nstate = next_state(state, Cmd.NOP, action)
            assert calc_opp_cmd(Cmd.NOP, state, nstate) == action

    def test_invalid_tostate(self):
        state = setup_state()
        nstate = setup_state()
        nstate.opponent.y = 2
        nstate.opponent.x = 100
        nstate.opponent.speed = 10

        assert calc_opp_cmd(Cmd.NOP, state, nstate) is None
