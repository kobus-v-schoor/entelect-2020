import json
import os
from collections import deque
from functools import lru_cache

from sloth.enums import Cmd
from sloth.state import State, Player, StateTransition, calc_opp_cmd, next_state
from sloth.maps import Map, GlobalMap
from sloth.search import search, offensive_search, score, Weights, opp_search
from sloth.ensemble import Ensemble
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

        self.ensemble = Ensemble(size=1000)

        self.search_depth = 3
        self.opp_search_depth = 2

    # waits for next round number and returns it
    def wait_for_next_round(self):
        try:
            return int(input())
        except EOFError:
            return -1

    # reads and returns the state json file. returns None if failed
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
        # get opponent's cmd
        cmd = calc_opp_cmd(trans.cmd, trans.from_state, trans.to_state)
        if cmd is None:
            log.error(f'unable to calculate opponent cmd for {trans.round_num}')
            return

        # keep track of opponent's mods
        calc_ns = next_state(trans.from_state, trans.cmd, cmd)
        calc_ns.opponent.transfer_mods(trans.to_state.opponent)

        # score ensemble and choose new opponent weights
        self.ensemble.update_scores(trans.from_state, cmd)
        self.opp_weights = self.ensemble.best_weights()

    # executes cmd for round_num
    def exec(self, round_num, cmd):
        if not type(cmd) is Cmd:
            cmd = Cmd(cmd)
        print(f'C;{round_num};{cmd}')

    # predicts the opponent's move based on the given state
    # NOTE only predicts movement and not offensive actions
    @lru_cache(maxsize=None)
    def pred_opp(self, state):
        if self.opp_search_depth == 0:
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

        return score(opp_search(state, max_search_depth=self.opp_search_depth),
                     state.switch(), self.opp_weights)[0]

    # returns the cmd that should be executed given the current state
    # done by doing a search for the best move
    def calc_cmd(self):
        if self.state.player.speed < 5:
            self.search_depth = 4
            self.opp_search_depth = 0
        elif self.state.player.speed < 8:
            self.search_depth = 3
            self.opp_search_depth = 2
        else:
            self.search_depth = 3
            self.opp_search_depth = 3

        search_res = search(self.state, self.pred_opp,
                            max_search_depth=self.search_depth)
        cmds = score(search_res, self.state, self.weights, self.pred_opp)
        cmd = cmds[0]

        if cmd == Cmd.NOP:
            cmd = offensive_search(self.state, cmds, self.pred_opp)

        # TODO update the global map if commands result in map changes for
        # later use by calc_opp_cmd

        return cmd

    def run(self):
        while True:
            # get the next round number
            round_num = self.wait_for_next_round()

            if round_num < 0:
                break

            # clear caches
            self.pred_opp.cache_clear()
            next_state.cache_clear()

            # read the state file
            raw_state = self.read_state(round_num)

            # parse raw state
            self.parse_state(round_num, raw_state)

            # check if game is finished
            if self.finished:
                break

            # calculate next cmd
            cmd = self.calc_cmd()
            self.prev_cmd = cmd

            # execute next cmd
            self.exec(round_num, cmd)
