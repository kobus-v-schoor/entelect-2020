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

        assert score(options, state, weights) == chosen[0]

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

        assert score(options, state, weights) == chosen[0]

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

    def test_oil_passage_block(self):
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

    def test_tweet_no_tweet(self):
        state = setup_state()
        state.player.tweets = 0

        assert offensive_search(state) == Cmd.NOP

    def test_tweet_behind(self):
        state = setup_state()

        state.player.tweets = 1
        state.player.x = 100
        state.opponent.x = 100
        assert offensive_search(state) == Cmd.NOP

        state.player.x = 90
        assert offensive_search(state) == Cmd.NOP

    def test_tweet_place_in_future_path(self):
        state = setup_state()
        state.player.tweets = 1

        state.player.x = 200

        state.opponent.y = 1
        state.opponent.x = 100
        pred = lambda s: Cmd.RIGHT

        nstate = next_state(state, Cmd.NOP, pred(state))
        nnstate = next_state(nstate, Cmd.NOP, pred(nstate))
        match = Cmd(Cmd.TWEET, pos=(nstate.opponent.x + 3, nnstate.opponent.y))

        assert offensive_search(state, pred_opp=pred) == match

    def test_tweet_dont_place_ahead_of_player(self):
        state = setup_state()
        state.player.tweets = 1

        state.player.y = 2
        state.player.x = 200

        state.opponent.y = 2
        state.opponent.x = 199

        pred = lambda s: Cmd.NOP

        assert offensive_search(state, pred_opp=pred) == Cmd.NOP

    def test_tweet_ignore_fix(self):
        state = setup_state()
        state.player.tweets = 1

        state.player.x = 100
        state.opponent.x = 10
        state.opponent.y = 4
        state.opponent.damage = 2

        def pred(state):
            if state.opponent.damage > 0:
                return Cmd.FIX
            return Cmd.LEFT

        nstate = next_state(state, Cmd.NOP, Cmd.LEFT)
        nnstate = next_state(nstate, Cmd.NOP, Cmd.LEFT)
        match = Cmd(Cmd.TWEET, pos=(nstate.opponent.x + 3, nnstate.opponent.y))

        assert offensive_search(state, pred_opp=pred) == match

    def test_dont_tweet_on_own_pos(self):
        state = setup_state()
        state.player.tweets = 1

        state.player.x = 200
        state.player.y = 2

        state.opponent.x = state.player.x - state.opponent.speed - 3
        state.opponent.y = state.player.y

        pred = lambda s: Cmd.NOP

        nstate = next_state(state, Cmd.NOP, pred(state))
        nnstate = next_state(nstate, Cmd.NOP, pred(nstate))
        assert nstate.opponent.y == state.player.y
        assert nstate.opponent.x + 3 == state.player.x

        match = Cmd(Cmd.TWEET, pos=(nstate.opponent.x + 2, nnstate.opponent.y))
        assert match.pos[0] == state.player.x - 1
        assert match.pos[1] == state.player.y
        assert offensive_search(state, pred_opp=pred) == match

    def test_emp_no_emp(self):
        state = setup_state()
        state.player.emps = 0

        state.player.x = 100
        state.player.y = 2

        state.opponent.x = 110
        state.opponent.y = 2

        assert offensive_search(state) == Cmd.NOP

    def test_emp_opp_behind(self):
        state = setup_state()
        state.player.emps = 1

        # behind
        state.player.x = 100
        state.player.y = 2

        state.opponent.x = 90
        state.opponent.y = 2

        assert offensive_search(state) == Cmd.NOP

        # same x
        state.opponent.x = 100
        state.opponent.y = 1

        assert offensive_search(state) == Cmd.NOP

    def test_emp_samelane(self):
        state = setup_state()
        state.player.emps = 1

        state.player.x = 100
        state.player.y = 2

        state.opponent.x = 150
        state.opponent.y = 2

        assert offensive_search(state) == Cmd.EMP

    def test_emp_min_max_lanes(self):
        state = setup_state()
        state.player.emps = 1

        state.player.x = 100
        state.player.y = 2

        state.opponent.x = 150
        state.opponent.y = 1

        assert offensive_search(state) == Cmd.EMP

        state.player.y = 3
        state.opponent.y = 4

        assert offensive_search(state) == Cmd.EMP

    def test_emp_outer_lanes(self):
        state = setup_state()
        state.player.emps = 1

        state.player.x = 100
        state.opponent.x = 150

        state.player.y = 1
        state.opponent.y = 2
        assert offensive_search(state) == Cmd.EMP

        state.player.y = 2
        state.opponent.y = 3
        assert offensive_search(state) == Cmd.EMP

        state.player.y = 4
        state.opponent.y = 3
        assert offensive_search(state) == Cmd.EMP

        state.player.y = 3
        state.opponent.y = 2
        assert offensive_search(state) == Cmd.EMP

    def test_emp_safety(self):
        state = setup_state()
        state.player.emps = 1

        state.player.x = 100
        state.player.y = 2

        state.opponent.x = 104
        state.opponent.y = 2

        assert state.player.x + state.player.speed >= state.opponent.x
        assert offensive_search(state) != Cmd.EMP
