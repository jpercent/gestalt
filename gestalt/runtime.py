import logging
import gestalt
import json
import multiprocessing
import optparse
import sys
import traceback

from gestalt.assembly import construct_application

__author__ = 'jpercent'

__all__ = ['Application', 'ConfigurationError', 'create', 'parse_options']

logger = logging.getLogger(__name__)


def parse_json_conf(conf):
    parsed_conf = None
    with open(conf, 'rt') as file_descriptor:
        json_string = file_descriptor.read()
        parsed_conf = json.loads(json_string)
    return parsed_conf


def create_application(conf_path):
    conf = parse_json_conf(conf_path)
    return construct_application(conf)


def create_background_context(conf_path):
    application = create_application(conf_path)
    assert 'main' in application
    application['main'].run()


def create_context(name, conf_path, background):
    if background:
        service = multiprocessing.Process(name=name, target=create_background_context, args=[conf_path])
        service.daemon = False
        service.start()
    else:
        create_background_context(conf_path)


def create(conf_path=None, name=None, async=False, background=False):
    if async:
        service = multiprocessing.Process(name=name, target=create_context, args=[name, conf_path, background])
        service.daemon = False
        service.start()
        return AsyncApplication(service, False if background else True)
    else:
        return create_application(conf_path)


class ConfigurationError(Exception):
    pass


def parse_options():

    usage = "usage: %prog --conf=<CONF-PATH> [options]"
    name_help = 'application name'
    conf_help = 'path to the configuration file'
    async_help = 'run in an asynchronous context; default value = false'
    background_help = 'background the asynchronous context; invalid without --async option; default value = false'
    try:
        parser = optparse.OptionParser(version="%prog 1.0", usage=usage)
        parser.add_option('-n', '--name', type=str, dest='name', default=None,
                          metavar='APP-NAME', help=name_help)
        parser.add_option('-c', '--conf', type=str, dest='conf_path', default=None,
                          metavar='CONF-PATH', help=conf_help)
        parser.add_option('-a', '--async', action='store_true', metavar='ASYNC',
                          help=async_help)
        parser.add_option('-b', '--background', action='store_false', metavar='BACKGROUND',
                          help=background_help)
        (options, args) = parser.parse_args()
        return options, args
    except Exception as e:
        logger.error('parse_options: FATAL failed to parse program arguments')
        logger.error(traceback.format_exc(limit=35))
        raise ConfigurationError(e)


class Application(object):
    def __init__(self):
        super(Application, self).__init__()

    def is_async(self):
        return False

    def run(self):
        """subclass hook"""


class AsyncApplication(Application):
    def __init__(self, subprocess=None, wait=True):
        super(AsyncApplication, self).__init__()
        self.subprocess = subprocess
        self.wait = wait

    def is_async(self):
        return True

    def run(self):
        if self.wait:
            self.subprocess.join()
        return


if __name__ == '__main__':
    if sys.platform == 'win32':
        multiprocessing.freeze_support()

    options, args = parse_options()
    app = create(**vars(options))
    app.run()
