# Entelect Challenge 2020

This is was my entry for the Entelect Challenge 2020, where the game was
Overdrive. The game was a two player racing game and the objective was
(unsurprisingly) to cross the finish line first. The game-engine that this bot
was designed to work with can be found
[here](https://github.com/EntelectChallenge/2020-Overdrive).

My entry made it to the finals where I placed 4th - the current state of the
repo was my exact submission to the finals.

## General approach

The basic idea on which the bot operated was to do an iterative-deepening tree
search (like most players did) to try and find an optimal move. Some
interesting features that the bot had were:

* For phase 1 and 2 the bot was able to try and learn its opponent's strategy
  using an ensemble approach. This worked okay-ish but in phase three it
  started to have diminishing returns and I disabled it improve the bot's
  performance
* The bot predicted the opponent by also doing a tree-search for them
* It was able to work out the opponent's cmds and also keep track of their
  powerups. It used this to make better predictions of the opponent's next move
* Optimization of the evaluation function was done by making incrementally
  smaller random changes to the evaluation function and calculating the average
  speed of the bot for a large number of games
* The bot only took offensive actions if it was not doing anything else, all
  the offensive logic can be found
[here](https://github.com/kobus-v-schoor/entelect-2020/blob/master/sloth/search.py#L158)
* Nearly all core parts were covered with unit tests which made development a
  lot easier in the final rounds since I didn't need to worry that I was
  breaking things

## Some cool things

* For the optimization I developed a multi-threaded runner which would deploy
  and run multiple games/game-engines concurrently which made optimization a
  lot easier and faster. I used a GCP VM with my free credits to run most of my
  optimizations.
* The tools folder includes a stats module which I used to pull detailed stats
  from a game's logs which I used in optimization
* In the tools there is an improved version of my public visualizer that added
  a bunch of features (stepping through the race, skipping to rounds, etc.)
  which helped me immensely during development

## What worked/didn't work

Some of the things that I think worked well:

* The automated unit testing was a huge help during development. Due to the
  nature of the tournament where there might pass a month or two between
  development it was crucial to help me develop without fear of breaking
  everything
* In the first and second stage the bot was developed to be as generic as
  possible to allow easily modifying it for the next rounds. By the third stage
  the changes needed for the EMPs and damage mechanic was minimal (around one
  or two hours of work)
* Staying active on the forum and the game-engine repo allowed me to stay on
  top of bugs and the newest developments, without it I'd probably run into
  quite a few issues

On the other hand, here are some things that didn't turn out so well:

* Using a GA approach to fine-tune the evaluation function didn't work well at
  all for me, I probably could have implemented it better but my final non-GA
  optimization approach worked better in the end
* Any decisions made on a whim usually turned out to be a problem. All the
  improvements that I made only truly helped when the statistics were on my
  side (more than 50 matches) due to the random nature of the game
