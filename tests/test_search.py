from sloth.search import search, opp_search, Weights, score, offensive_search
from sloth.state import Player, State, next_state, valid_actions
from sloth.maps import GlobalMap, Map
from sloth.enums import Cmd, Speed, Block

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


class TestSearch:
    def test_validity(self):
        state = setup_state()
        opp_pred = lambda s: Cmd.ACCEL

        options = search(state, opp_pred, 4)

        for actions, final_state in options:
            cur_state = state
            for action in actions:
                cur_state = next_state(cur_state, action, opp_pred(cur_state))
            assert cur_state == final_state

    def test_opp_search_validity(self):
        state = setup_state()
        options = opp_search(state)

        state = state.switch()
        pred = lambda s: Cmd.ACCEL

        for actions, final_state in options:
            cur_state = state
            for action in actions:
                cur_state = next_state(cur_state, action, pred(cur_state))
            assert cur_state == final_state

class TestScore:
    def test_score_normal(self):
        state = setup_state()
        options = []
        for action in valid_actions(state):
            options.append(([action], setup_state()))

        chosen = options[1]
        chosen[1].player.speed = 100

        weights = Weights({
            'pos': 0,
            'speed': 1,
            'boosts': 0,
            'oils': 0,
            'lizards': 0,
            'tweets': 0,
            'score': 0,
        })

        assert score(options, state, weights) == chosen[0][0]

    def test_score_endgame(self):
        state = setup_state()
        options = []
        for action in valid_actions(state):
            options.append(([action], setup_state()))

        # decoys
        options[0][1].player.x = 1550
        options[1][1].player.x = 1400
        options[1][1].player.speed = 1000

        chosen = options[2]
        chosen[1].player.x = 1500
        chosen[1].player.speed = 100

        weights = Weights({
            'pos': 1,
            'speed': 0,
            'boosts': 0,
            'oils': 0,
            'lizards': 0,
            'tweets': 0,
            'score': 0,
        })

        assert score(options, state, weights) == chosen[0][0]

class TestOffensiveSearch:
    def test_nop(self):
        state = setup_state()
        assert offensive_search(state) == Cmd.NOP

    def test_excessive_oil_drop(self):
        state = setup_state()
        state.player.y = 2
        state.player.oils = 4

        assert offensive_search(state) == Cmd.OIL

    def test_right_behind_oil_drop(self):
        state = setup_state()
        state.player.x = 10
        state.player.y = 2
        state.player.oils = 1
        state.opponent.x = state.player.x - 1
        state.opponent.y = state.player.y

        assert offensive_search(state) == Cmd.OIL

    def test_close_behind_oil_drop(self):
        state = setup_state()
        state.player.x = 100
        state.player.y = 2
        state.player.oils = 1
        state.opponent.x = state.player.x - 10
        state.opponent.y = state.player.y

        assert offensive_search(state) == Cmd.OIL

    def test_passage_block(self):
        state = setup_state()

        state.player.oils = 1
        x = 100
        y = 2

        def set_xy(_x, _y):
            x = _x
            y = _y
            state.player.x = x
            state.player.y = y

        assert offensive_search(state) == Cmd.NOP

        set_xy(x, 1)
        assert offensive_search(state) == Cmd.OIL

        set_xy(x, 4)
        assert offensive_search(state) == Cmd.OIL

        set_xy(x, 2)
        state.map[x, y - 1] = Block.MUD
        state.map[x, y + 1] = Block.MUD
        assert offensive_search(state) == Cmd.OIL
