import json
import os

from enums import Cmd

class Bot:
    def __init__(self):
        self.finished = False

    # waits for next round number and returns it
    def wait_for_next_round(self):
        return int(input())

    # reads and returns the state json file. returns None if failed
    def read_state(self, round_num):
        state_file = os.path.join('rounds', str(round_num), 'state.json')
        with open(state_file, 'r') as f:
            return json.load(f)

    def parse_state(self, raw_state):
        if raw_state['player']['state'] == 'FINISHED':
            self.finished = True
            return

    # executes cmd for round_num
    def exec(self, round_num, cmd):
        print(f'C;{round_num};{cmd.value}')

    # returns the cmd that should be executed given the current state
    # done by doing a search for the best move
    def find_cmd(self):
        return Cmd.ACCEL

    def run(self):
        while True:
            # get the next round number
            round_num = self.wait_for_next_round()

            # read the state file
            raw_state = self.read_state(round_num)

            # parse raw state
            self.parse_state(raw_state)

            # check if game is finished
            if self.finished:
                break

            # execute next cmd
            self.exec(round_num, self.find_cmd())
