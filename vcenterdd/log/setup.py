
import sys
import logging
import logging.config
import logging.handlers
import yaml
from pathlib import Path


class LoggerSetup(object):

    def __init__(self, yaml_file, auto_setup=False):
        self.config_file = yaml_file
        self._init_dictConfig()

        if auto_setup:
            self.setup()

    def _init_dictConfig(self):
        with open(self.config_file, 'rt') as f:
            conf = yaml.safe_load(f.read())
            f.close()
        self.dictConfig = conf

    def setup(self):
        self.__validate_fpath_structure()
        logging.config.dictConfig(self.dictConfig)

    def __validate_fpath_structure(self):
        """ internal method to locate and pre-create log file structures"""

        for h in self.dictConfig.get('handlers' or None):
            handler = self.dictConfig['handlers'].get(h)
            if handler.get('filename' or None):
                fpath = Path(handler['filename'])
                if not fpath.exists():
                    fpath.parent.mkdir(exist_ok=True, parents=True)

    def set_loglevel(self, loglevel='INFO', exclude_loggers=None):
        if exclude_loggers and (not isinstance(exclude_loggers, list) and not isinstance(exclude_loggers, tuple)):
            raise TypeError("parameter exclude_loggers expected a list of logger names to exclude")
        elif exclude_loggers and (isinstance(exclude_loggers, list) or isinstance(exclude_loggers, tuple)):
            for l in self.dictConfig.get('loggers'):
                if l not in exclude_loggers:
                    self.dictConfig.get('loggers').get(l)['level'] = loglevel.upper()
        else:
            for l in self.dictConfig.get('loggers'):
                self.dictConfig.get('loggers').get(l)['level'] = loglevel.upper()


def addClassLogger(cls: type, log_var='__log'):
    cls_attr = '_{}{}'.format(cls.__name__, log_var)
    setattr(cls, cls_attr, logging.getLogger(cls.__module__ + '.' + cls.__name__))
    return cls
