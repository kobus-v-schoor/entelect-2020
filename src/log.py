import logging

logging.basicConfig(format='%(levelname)s: %(message)s', filename='bot.log',
        filemode='w', level=logging.INFO)
log = logging.getLogger()
