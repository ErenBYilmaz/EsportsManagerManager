import os
import logging
import sys

# noinspection PyUnresolvedReferences
import __main__

logging = logging
try:
    logfile = 'logs/' + os.path.normpath(__main__.__file__).replace(os.path.abspath('.'),'') + '.log'
except AttributeError:
    print('WARNING: unable to set log file path.')
else:
    try:
        os.makedirs(os.path.dirname(logfile), exist_ok=True)
        logging.basicConfig(level=logging.DEBUG, filename=logfile, filemode="a+",
                            format="%(asctime)-15s %(levelname)-8s %(message)s")
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    except OSError:
        print('WARNING: unable to set log file path.')