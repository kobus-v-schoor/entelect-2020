# Author: Kobus van Schoor

import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

class Bot:
    def __init__(self):
        pass

    def wait_for_next_round(self):
        log.debug('waiting for next round')
        self.next_round = int(input())
        log.debug(f'next round read as {self.next_round}')

    def read_state(self):
        pass

    def run(self):
        log.info('bot started')

        while True:
            self.wait_for_next_round()
            self.read_state()


if __name__ == '__main__':
    log.info('starting bot')
    bot = Bot()
    bot.run()
