import site
import os

if __name__ == '__main__':
    mod = os.path.dirname(os.path.realpath(__file__))
    site.addsitedir(os.path.dirname(mod))

from sloth.bot import Bot

if __name__ == '__main__':
    bot = Bot()
    bot.run()
