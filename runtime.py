import logging
import json
import sys
import traceback

from gestalt.injector import DependencyInjector

__author__ = 'jpercent'


class RuntimeAssistant(object):
    def __init__(self):
        super(RuntimeAssistant, self).__init__()

    @staticmethod
    def configure(config, factory_instance):
        assert factory_instance
        dpi = DependencyInjector(factory_instance)
        instance = dpi.configure_application(config)
        assert instance
        return instance

    @staticmethod
    def parse_json_config(conf):
        with open(conf, 'rt') as file_descriptor:
            json_string = file_descriptor.read()
            config = json.loads(json_string)
        return config

    @staticmethod
    def make_high_priority():
        try:
            import psutil
            import os
            p = psutil.Process(os.getpid())
            p.set_nice(psutil.HIGH_PRIORITY_CLASS)
        except Exception as e:
            RuntimeAssistant.print_last_exception()

    @staticmethod
    def print_last_exception():
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)


class JsonConfiguredRuntime(object):
    def __init__(self, factory, conf_dir):
        """Initializes a JsonConfiguredRuntime."""
        self.factory = factory
        self.conf_dir = conf_dir
        self.full_conf_path = None
        self.logger = None
        self.log_level = logging.INFO
        self.config = None
        self.controller = None
        self.args = None
        self.options = None

    def init(self):
        try:
            self.config = RuntimeAssistant.parse_json_config(self.full_conf_path)
            self.controller = RuntimeAssistant.configure(self.config, self.factory)
            self.logger = logging.getLogger(__name__)
        except Exception as e:
            if not self.logger:
                print(str(self.__class__.__name__)+': FATAL failed to initialize correctly; did not complete logging setup')
            else:
                self.logger.fatal('failed to initialize correctly')

            RuntimeAssistant.print_last_exception()
            raise e


class Controller(object):
    def __init__(self):
        super(Controller, self).__init__()

    def start(self, **kwargs):
        # Subclass hook
        pass

