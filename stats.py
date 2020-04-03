#! /usr/bin/env python3

import os
import csv
import math

runs = [] # boost runs
speeds = []
matches = 0
rounds = 0

for match in os.listdir('.'):
    matches += 1
    with open(os.path.join(match, 'A - sonic-sloth.csv'), 'r') as csvfile:
        reader = csv.reader(csvfile)
        count = 0
        for row in reader:
            speed = int(row[4])
            speeds.append(speed)
            cmd = row[5]
            if cmd == 'USED_BOOST':
                count = 1

            if count:
                if speed != 15:
                    runs.append(count)
                    count = 0
                elif cmd != 'USED_BOOST':
                    count += 1
            rounds += 1

avg_rounds = rounds/matches
avg_speed = sum(speeds)/len(speeds)
avg_boosts_used = len(runs)/matches
avg_boost_length = sum(runs)/len(runs)

print("avg rounds:", avg_rounds)
print("avg speed:", round(avg_speed, 3))
print("avg boosts used per match:", avg_boosts_used)
print("avg boost length:", round(avg_boost_length, 3))

avg_boost = avg_boosts_used * 5 # how many rounds we could've been boosting
avg_non_boost = avg_rounds - avg_boost # how many rounds we weren't boosting

avg_boost /= avg_rounds # ratio of rounds boosting
avg_non_boost /= avg_rounds # ratio of rounds not boosting

theoretical_best = 1500 / ((avg_boost * 15) + (avg_non_boost * 9))

print("theoretical best rounds:", round(theoretical_best, 2))
print("theoretical improvement possible:", round(avg_rounds - theoretical_best, 2))
