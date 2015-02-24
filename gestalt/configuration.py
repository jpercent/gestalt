# Copyright 2015 James Percent and Gestalt contributors.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
from optparse import OptionParser
import importlib
import json
import logging
import os
import sys
import traceback


__author__ = 'jpercent'


class Configuration(object):
    def __init__(self, conf=None):
        self.raw_conf = conf

    def parse_json_conf(self, conf=None):
        if not conf:
            assert self.raw_conf
            conf = self.raw_conf

        with open(conf, 'rt') as file_descriptor:
            json_string = file_descriptor.read()
            parsed_conf = json.loads(json_string)
        return parsed_conf

    def parse_options(self, default_path):
        usage = "usage: %prog [options]"
        conf_help = 'path to the configuration; if not set conf.json is used'
        try:
            parser = OptionParser(version="%prog 1.0", usage=usage)
            default_conf = os.path.join(default_path, 'conf.json')
            parser.add_option('-c', '--conf', type=str, dest='conf', default=default_conf, metavar='CONF', help=conf_help)
            (options, args) = parser.parse_args()
            return options, args
        except Exception as e:
            print('parse_options: FATAL failed to parse program arguments')
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
            raise e

    def parse(self):
        default_path = os.path.dirname(os.path.realpath( __file__ ))
        options, args = self.parse_options(default_path)
        common_conf = self.parse_json_conf(conf=os.path.join(default_path, 'common.json'))
        conf = self.parse_json_conf(options.conf)
        common_conf.update(conf)
        return conf

    def configure_logging(**config):
        if config:
            logging.config.dictConfig(config)
        else:
            level = logging.DEBUG
            logging.basicConfig(level=level)

        return logging.getLogger(__name__)


class GestaltFactory(object):
    def __init__(self):
        super(GestaltFactory, self).__init__()

    def get_function(self, string):
        parts = string.split('.')
        count = 0

        if len(parts) <= 1:
            return globals()[string]

        cursor = importlib.import_module(parts[count])
        count += 1
        while count < len(parts):
            cursor = getattr(cursor, parts[count])
            count += 1

        return cursor

    def create(self, instance_name, config):
        objdesc = config[instance_name]
        deps = None
        args = None

        assert objdesc['type']

        obj_type = objdesc['type']

        if 'args' in objdesc:
            args = objdesc['args']

        if 'deps' in objdesc:
            deps = {}

            for key, value in objdesc['deps'].items():
                if type(value) == list:
                    depobj = []
                    for element in value:
                        depobj.append(self.create(element, config))
                else:
                    depobj = self.create(value, config)

                deps[key] = depobj

            if args and deps:
                args.update(deps)
            elif deps.keys():
                assert not args
                args = deps

        function = self.get_function(obj_type)
        if args:
            newobj = function(**args)
        else:
            newobj = function()

        if not newobj:
            self.logger.error("gestalt.AbstractFactory.create "+str(obj_type), "failed; objdesc = ", objdesc)

        assert newobj
        return newobj


class Assembler(object):
    def __init__(self, factory=None):
        super(Assembler, self).__init__()
        self.factory = factory
        self.services = []
        self.controller = None

    def configure_application(self, config, factory=None):
        assert (factory or self.factory) and config

        if not factory:
            factory = self.factory

        self.configure_services(config, factory)
        assert self.controller
        return self.controller

    def configure_services(self, config, factory):
        level = 0
        max_level = 0

        while level <= max_level:

            pop_keys = set([])
            for key, value in config.items():
                if not 'service' in value:
                    continue

                level_value = value['service']
                if level_value > max_level:
                    max_level = level_value

                if level_value <= level:
                    service = factory.create(key, config)
                    self.services.append(service)
                    if 'controller' in config[key]:
                        self.controller = factory.create(key, config)

                    pop_keys.add(key)

            for key in pop_keys:
                config.pop(key)

            level += 1

