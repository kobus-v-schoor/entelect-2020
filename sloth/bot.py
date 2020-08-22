import json
import os
from collections import deque
from functools import lru_cache

from sloth.enums import Cmd, Block, boost_speed
from sloth.state import State, Player, StateTransition, calc_opp_cmd, next_state
from sloth.state import ns_filter
from sloth.maps import Map, GlobalMap, clean_map
from sloth.search import search, offensive_search, score, Weights, opp_search
# from sloth.ensemble import Ensemble
from sloth.log import log

class Bot:
    def __init__(self):
        self.finished = False
        self.global_map = GlobalMap(x_size=1500, y_size=4)

        self.prev_state = None
        self.state = None
        # will hold the state transitions that need to be processed to calculate
        # opponent's cmds
        self.backlog = deque()

        with open('weights.json', 'r') as f:
            self.weights = Weights(json.load(f))
        self.opp_weights = self.weights

        # self.ensemble = Ensemble(size=1000)

        self.search_depth = 3
        self.opp_search_depth = 2

        self.ct_pos = None

    # waits for next round number and returns it
    def wait_for_next_round(self):
        try:
            return int(input())
        except EOFError:
            return -1

    # reads and returns the json state file
    def read_state(self, round_num):
        state_file = os.path.join('rounds', str(round_num), 'state.json')
        with open(state_file, 'r') as f:
            return json.load(f)

    def parse_state(self, round_num, raw_state):
        # check if game is finished
        if raw_state['player']['state'] == 'FINISHED':
            self.finished = True
            return

        # save previous state
        self.prev_state = self.state

        # create state
        self.state = State()

        # parse map
        self.state.map = Map(raw_state['worldMap'], self.global_map)

        # parse players
        self.state.player = Player(raw_state['player'])
        self.state.opponent = Player(raw_state['opponent'])

        # backlog state transition
        if self.prev_state is not None:
            # save state transition in backlog
            self.backlog.append(StateTransition(round_num - 1, self.prev_cmd,
                self.prev_state, self.state))

            while self.backlog:
                # opponent's entire move is within our view
                if self.backlog[0].to_state.opponent.x <= self.state.map.max_x:
                    self.process_opp_action(self.backlog.popleft())
                else:
                    break

    def process_opp_action(self, trans):
        # clean map of stuff that wasn't there when the opponent was here
        if trans.from_state.opponent.x >= trans.from_state.player.x:
            clean_map(trans.from_state, trans.from_state.opponent.x,
                      trans.to_state.opponent.x)

        # check if we have lost track of the opponent's damage - if their x
        # offset or final speed is more than they should be allowed decrease
        # their damage until their move becomes valid
        x_off = trans.to_state.opponent.x - trans.from_state.opponent.x
        if trans.from_state.opponent.y != trans.to_state.opponent.y:
            x_off += 1
        fspeed = trans.to_state.opponent.speed

        dmg = max(trans.from_state.opponent.damage, 0)
        while max(x_off, fspeed) > boost_speed(dmg) and dmg > 0:
            dmg -= 1
        trans.from_state.opponent.damage = dmg

        # get opponent's cmd
        cmd = calc_opp_cmd(trans.cmd, trans.from_state, trans.to_state)
        if cmd is None:
            log.error(f'unable to calculate opponent cmd for {trans.round_num}')
            trans.from_state.opponent.transfer_mods(trans.to_state.opponent)
            return

        # keep track of opponent's mods
        calc_ns = next_state(trans.from_state, ns_filter(trans.cmd), cmd)
        opp = trans.to_state.opponent
        calc_ns.opponent.transfer_mods(opp)
        opp.lizards = max(opp.lizards, 0)
        opp.boosts = max(opp.boosts, 0)

        # remove crashed into cybertrucks
        if trans.from_state.opponent.x < trans.from_state.player.x:
            calc_ns.map.update_global_map()

        # score ensemble and choose new opponent weights
        # self.ensemble.update_scores(trans.from_state, cmd)
        # self.opp_weights = self.ensemble.best_weights()

    # executes cmd for round_num
    def exec(self, round_num, cmd):
        if not type(cmd) is Cmd:
            cmd = Cmd(cmd)
        print(f'C;{round_num};{cmd}')

    # just a thin wrapper to include the search depth
    def pred_opp(self, state):
        return self._pred_opp(state, self.opp_search_depth)

    # predicts the opponent's move based on the given state
    # NOTE only predicts movement and not offensive actions
    @lru_cache(maxsize=None)
    def _pred_opp(self, state, search_depth):
        if search_depth == 0:
            return Cmd.ACCEL

        # if opponent is outside our view just assume they are accelerating
        # since we won't be able to predict anything better than that
        if state.opponent.x >= self.state.map.max_x:
            return Cmd.ACCEL

        # if we are stuck behind the opponent and they are standing still
        # assume they are being mean and are trying to block us
        if ((state.player.x, state.player.y) == (state.opponent.x - 1,
            state.opponent.y) and state.opponent.speed == 0):
            return Cmd.NOP

        return score(opp_search(state, max_search_depth=search_depth),
                     state.switch(), self.opp_weights)[0]

    # returns the cmd that should be executed given the current state
    # done by doing a search for the best move
    def calc_cmd(self):
        if self.state.player.speed < 5:
            self.search_depth = 4
            self.opp_search_depth = 0
        elif self.state.player.speed < 8:
            self.search_depth = 3
            self.opp_search_depth = 1
        else:
            self.search_depth = 3
            self.opp_search_depth = 2

        search_res = search(self.state, self.pred_opp,
                            max_search_depth=self.search_depth)
        cmds = score(search_res, self.state, self.weights, self.pred_opp)
        cmd = cmds[0]

        if cmd == Cmd.NOP:
            # increase search depth for better opponent prediction in offensive
            # search
            self.opp_search_depth = 3
            cmd = offensive_search(self.state, cmds, self.pred_opp)

            # place oil block on map if we're dropping oil
            if cmd == Cmd.OIL:
                x, y = self.state.player.x, self.state.player.y
                self.state.map.global_map[x, y] = Block.OIL_SPILL

        return cmd

    def run(self):
        self.prev_cmd = Cmd.NOP

        while True:
            # get the next round number
            round_num = self.wait_for_next_round()

            if round_num < 0:
                break

            # clear caches
            self._pred_opp.cache_clear()
            next_state.cache_clear()

            # read the state file
            raw_state = self.read_state(round_num)

            # parse raw state
            self.parse_state(round_num, raw_state)

            # place cybertruck from previous round onto map
            if self.prev_cmd == Cmd.TWEET:
                # remove our previously placed cybertruck
                if self.ct_pos is not None:
                    x, y = self.ct_pos
                    block = self.state.map.global_map[x, y].get_underlay()
                    self.state.map.global_map[x, y] = block
                # place new cybertruck
                x, y = self.prev_cmd.pos
                self.state.map.global_map[x, y].set_cybertruck()
                self.ct_pos = (x, y)

            # check if game is finished
            if self.finished:
                break

            # calculate next cmd
            cmd = self.calc_cmd()
            self.prev_cmd = cmd

            # execute next cmd
            self.exec(round_num, cmd)
