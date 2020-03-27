#! /usr/bin/env python3

import os
import json

speeds = []

for r in os.listdir('.'):
    with open(os.path.join(r, 'state.json')) as f:
        state = json.load(f)
        speeds.append(int(state['player']['speed']))

print('average speed:', sum(speeds)/len(speeds))
