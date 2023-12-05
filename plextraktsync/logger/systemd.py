import logging
import random
import time

try:
    from cysystemd.journal import JournaldLogHandler
except ImportError:
    pass

# get an instance of the logger object this module will use
logger = logging.getLogger(__name__)

# instantiate the JournaldLogHandler to hook into systemd
journald_handler = JournaldLogHandler()

# set a formatter to include the level name
journald_handler.setFormatter(logging.Formatter(
    '[%(levelname)s] %(message)s'
))

# add the journald handler to the current logger
logger.addHandler(journald_handler)

# optionally set the logging level
logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    print("logger:", logger)
    while True:
        # log a sample event
        logger.info(
            'test log event to systemd! Random number: %s',
            random.randint(0, 10)
        )

        # sleep for some time to not saturate the journal
        time.sleep(5)
