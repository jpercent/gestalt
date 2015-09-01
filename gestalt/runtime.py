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


def parse_json_conf(conf, override_values=None):
    parsed_conf = None
    with open(conf, 'rt') as file_descriptor:
        json_string = file_descriptor.read()
        parsed_conf = json.loads(json_string)

    return parsed_conf


def load_includes(conf):
    ret = {}
    if 'includes' in conf:
        includes = conf['includes']
        files = includes.keys()
        for file in files:
            with open(file, 'rt') as fd:
                json_string = fd.read()
                new_include = json.loads(json_string)

            if not new_include:
                continue

            for type in includes[file]:
                assert type in new_include
                new_type = new_include[type]
                assert not(type in ret)
                ret[type] = new_type

            if 'global_values' in new_include:
                if 'global_values' in conf:
                    new_include['global_values'].update(conf['global_values'])

                conf['global_values'] = new_include['global_values']

        conf.pop('includes')
    return ret


def parse_override_values(override_values):
    ret = None
    if override_values:
        ret = json.loads('{'+override_values+'}')

    return ret


def create_application(conf_path=None, override_values=None):
    conf = parse_json_conf(conf_path)
    includes = load_includes(conf)
    assert len(set(conf.keys()).intersection(includes.keys())) == 0
    conf.update(includes)
  #  print("global values = ", conf['global_values'])
    if override_values and 'global_values' in conf:
        global_values = conf['global_values']
        overrides = parse_override_values(override_values)
        global_values.update(overrides)
        print("global_values = ", global_values)

        print("override values present\n")
    else:
        print('override values not present')

#    print('gloable values =', conf['global_values'])
 #   sys.exit(0)


    return construct_application(conf)


def create_background_context(conf_path=None, override_values=None):
    application = create_application(conf_path=conf_path, override_values=override_values)
    assert 'main' in application
    application['main'].run()


def create_context(name, conf_path, background, override_values=None):
    if background:
        service = multiprocessing.Process(name=name, target=create_background_context,
                                          args=[conf_path, override_values])
        service.daemon = False
        service.start()
    else:
        create_background_context(conf_path, override_values=override_values)


def create(conf_path=None, name=None, async=False, background=False, override_values=None):
    if async:
        # double fork love...
        service = multiprocessing.Process(name=name, target=create_context,
                                          args=[name, conf_path, background,
                                                override_values])
        service.daemon = False
        service.start()
        return AsyncApplication(service, False if background else True)
    else:
        return create_application(conf_path=conf_path, override_values=override_values)


class ConfigurationError(Exception):
    pass


def parse_options():

    usage = "usage: %prog --conf=<CONF-PATH> [options]"
    name_help = 'application name'
    conf_help = 'path to the configuration file'
    override_help = 'comma separated list of colon separated key:value pairs that override config values'
    async_help = 'run in an asynchronous context; default value = false'
    background_help = 'background the asynchronous context; invalid without --async option; default value = false'
    try:
        parser = optparse.OptionParser(version="%prog 1.0", usage=usage)
        parser.add_option('-n', '--name', type=str, dest='name', default=None,
                          metavar='APP-NAME', help=name_help)
        parser.add_option('-c', '--conf', type=str, dest='conf_path', default=None,
                          metavar='CONF-PATH', help=conf_help)
        parser.add_option('-o', '--override', type=str, dest='override_values', default=None,
                          metavar='OVERRIDE', help=override_help)
        parser.add_option('-a', '--async', action='store_true', metavar='ASYNC',
                          help=async_help)
        parser.add_option('-b', '--background', action='store_false', metavar='BACKGROUND',
                          help=background_help)
        (options, args) = parser.parse_args()
        #assert options.name and options.conf_path
        return options, args
    except Exception as e:
        logger.error('parse_options: FATAL failed to parse program arguments')
        logger.error(traceback.format_exc(limit=35))
        #exc_type, exc_value, exc_traceback = sys.exc_info()
        #traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        raise ConfigurationError(e)


class Application(object):
    def __init__(self):
        super(Application, self).__init__()

    def is_async(self):
        return False

    def run(self):
        """subclass hook"""

    def __call__(self):
        return self.run()


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
