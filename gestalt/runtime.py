import logging
import gestalt
import json
import multiprocessing
import optparse
import sys
import traceback


__author__ = 'jpercent'

__all__ = [Application, create]

logger = logging.getLogger(__name__)


def parse_json_conf(conf):
    parsed_conf = None
    with open(conf, 'rt') as file_descriptor:
        json_string = file_descriptor.read()
        parsed_conf = json.loads(json_string)
    return parsed_conf


def create_application(conf_path):
    conf_obj = gestalt.Configuration(conf_path)
    conf = conf_obj.parse()
    factory = gestalt.Factory()
    assembler = gestalt.Assembler(conf, factory)
    return assembler.construct_application()


def create_background_context(conf_path):
    application = create_application(conf_path)
    assert application.main
    application.run()


def create_context(name, conf_path, background):
    if background:
        service = multiprocessing.Process(name=name, target=create_background_context, args=[conf_path])
        service.daemon = False
        service.start()
    else:
        create_background_context(conf_path)


def create(name, conf_path, async=True, background=False):
    if async:
        service = multiprocessing.Process(name=name, target=create_context, args=[name, conf_path, background])
        service.daemon = False
        service.start()
        return service
    else:
        return create_application(name, conf_path)


def parse_options():

    usage = "usage: %prog --name=<APP-NAME> --conf=<CONF-PATH> [options]"
    name_help = 'application name'
    conf_help = 'path to the configuration file'
    async_help = 'run in an asynchronous context; default value = false'
    background_help = 'background the asynchronous context; invalid without --async option; default value = false'
    try:
        parser = optparse.OptionParser(version="%prog 1.0", usage=usage)
        parser.add_option('-n', '--name', type=str, dest='name', default=None, metavar='APP-NAME', help=name_help)
        parser.add_option('-c', '--conf', type=str, dest='conf', default=None, metavar='CONF-PATH', help=conf_help)
        parser.add_option('-a', '--async', action='store_true', metavar='ASYNC', help=async_help)
        parser.add_option('-b', '--background', action='store_false', metavar='BACKGROUND', help=background_help)
        (options, args) = parser.parse_args()
        assert options.name and options.conf
        return options, args
    except Exception as e:
        logger.error('parse_options: FATAL failed to parse program arguments')
        logger.error(traceback.format(limit=35))
        #exc_type, exc_value, exc_traceback = sys.exc_info()
        #traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        raise e


class Application(object):
    def __init__(self):
        super(Application, self).__init__()

    def run(self):
        """subclass hook"""

if __name__ == '__main__':
    if sys.platform == 'win32':
        multiprocessing.freeze_support()

    options, args = parse_options()
    app = create(options.name, options.conf, options.async, options.background)
    app.run()
