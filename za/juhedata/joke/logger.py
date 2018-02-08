import logging
from logging.handlers import TimedRotatingFileHandler
import conf
import sys
import os

LOGFORMAT = '[%(asctime)s] %(message)s'
BACKCOUNT = 15

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def initLogger(path):
    global logger
    if not logger.handlers:
        handler = logging.handlers.TimedRotatingFileHandler(path + os.sep + 'worker.log', when='midnight', interval=1, backupCount=BACKCOUNT)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    if conf.DEBUG_MODE:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)


