# Stage 1

## Available powerups

* Boosts (boosts speed to 15 for 5 rounds or until you hit an obstacle)
* Oil items (allows you to drop an oil spill block)

## Map obstacles

* Mud (reduces speed by one level)
* Oil spill (reduces speed by one level)

## Exploitable rules

* If your on the max speed, you can go over one obstacle without actually
  losing speed, since you can just re-accelerate the next round
* You can increase your score by dropping unused oil spills instead of doing
  nothing

## General approach

* A iterative deepening tree search was used to consider all valid moves until
  either the moves resulted in moving outside of the car's view or a max depth
  was reached
* The final move was chosen by scoring the final state by weighting various
  properties of that state - these properties were:
  * Speed (high weight)
  * How far the car would have moved (high weight)
  * Increase in score (low weight)
  * The opponent's position advancement (low weight)
  * The opponent's speed (low weight)
  * The opponent's score (low weight)
* Final weightings for the above properties was chosen by hand by
  experimentally playing games (see section on what didn't work for reason)
* A model of the opponent was built during gameplay by using an ensemble
  approach which worked on the assumption that most opponents would probably be
  using some variation on a tree search algorithm. Score weightings (as
  explained above) that made correct predictions of the opponent was rewarded,
  with the weightings that had the highest score being used to predict the
  opponent
* Opponent's move was also predicted using the same tree search algorithm

## Things that worked

* The ensemble approach seems to have been a good model for predicting the
  opponent's moves.
* Tree-search algorithm was definitely the way to go - produced pseudo-optimal
  solutions that is easy to optimize
* Predicting the opponent allowed was very important for offensive gameplay -
  without it it would've been very hard to use oils and zig-zag (collision
  logic used to block opponent) effectively
* Tree-search algorithm was able to effectively run even with Python code given
  that there are relatively few moves that need to be considered

## Things that didn't work

* Optimizing the score weightings using a evolutionary algorithm turned out to
  be a bust. This was probably due to the fact that the individuals was only
  played against other randomly generated individuals.
* Approaches that used traditional machine-learning algorithms to attempt to
  build a model of the opponent during gameplay didn't work. Even though it was
  able to train while waiting for the opponent without timing out, the very
  low number of samples made for very poor models (most of the time only
  predicting one move)
* For some reason, whenever decelerating was allowed, every now and then the
  car would go and stop right before the opponent and just stop, blocking the
  other player and stopping the game. I couldn't get this eliminated even with
  score penalties for stopping. Decelerating thus had to be disabled as a valid
  move

## Improvements to make in the next phase

* Automated optimization of the score weightings is needed. Some approach using
  an already well-performing score weighting and optimizing that will be needed
