#!/usr/bin/python

# environment prep
import os
import sys
import logging
import logging.config
import logging.handlers
import yaml

with open('/root/vcenterdd/logging_config.yml', 'rt') as f:
    conf = yaml.safe_load(f.read())
    f.close()
dictConfig = conf
logging.config.dictConfig(dictConfig)
logger = logging.getLogger(__name__)

logger.info('Starting imports of custom modules')

import argparse
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
parent_dir = BASE_DIR.replace(os.path.basename(BASE_DIR), '')
sys.path.append(BASE_DIR)
if os.environ.get('VMWARE_PYTHON_PATH' or None):
    sys.path.extend(os.environ['VMWARE_PYTHON_PATH'].split(';'))

logger.debug(sys.path)

# Continue setup
logger.debug("Importing LoggerSetup")
from vcenterdd.log.setup import LoggerSetup
logger.debug("Importing Datadog")
from vcenterdd.datadog.handle import Datadog
logger.debug("Importing VcenterAlarm")
from vcenterdd.alarm.handle import VcenterAlarm

try:
    parser = argparse.ArgumentParser(description="Arguments passed in from vCenter")
    parser.add_argument('-e', '--env',
                        required=True, action='store')
    parser.add_argument('-debug', '--debug',
                        required=False, action='store_true',
                        help='Used for Debug level information')
    cmd_args = parser.parse_args()
except BaseException as e:
    logger.exception('Exception: {} \n Args: {}'.format(e, e.args))

if cmd_args.debug:
    LOGLEVEL = 'DEBUG'
else:
    LOGLEVEL = 'INFO'

try:
    logger.debug("LoggerSetup")
    log_setup = LoggerSetup(yaml_file='{}/vcenterdd/logging_config.yml'.format(BASE_DIR))
    log_setup.set_loglevel(loglevel=LOGLEVEL)
    log_setup.setup()
    logger.debug("LoggerSetup Complete")
except BaseException as e:
    logger.exception('Exception: {} \n Args: {}'.format(e, e.args))

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    try:
        logger.info("Starting datadog alarm forwarder")

        alarm = VcenterAlarm(env=cmd_args.env)
        alarm.format_datadog_event()
        dd = Datadog('{}/vcenterdd/datadog_config.conf'.format(BASE_DIR))
        logger.info("Sending JSON Data: \n{}".format(alarm.datadog_format.__str__()))
        dd.post_event(**alarm.datadog_format)
        logger.info("Alarm Forwarder complete")
    except BaseException as e:
        logger.exception('Exception: {} \n Args: {}'.format(e, e.args))
        raise e

