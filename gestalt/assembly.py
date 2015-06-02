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

import importlib
import logging
import json

__author__ = 'jpercent'

__all__ = ['construct_application']

logger = logging.getLogger(__name__)


def get_factory_method(string):
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


def spawn(qualified_type_name, args):
    function = get_factory_method(qualified_type_name)
    if args:
        newobj = function(**args)
    else:
        newobj = function()

    if not newobj:
        logger.error("failed to create {type}; arguments = {args}".format(type=qualified_type_name, args=args))
        raise Exception("cannot create object type = {type}, arguments = {args}".format(type=qualified_type_name, args=args))

    return newobj


def create_instance(instance_name, conf, services, spawn_fn=spawn):
#    print("instance = ", instance_name)
#    print("services = ", services)
#    print("conf =", conf.keys())
    objdesc = conf[instance_name]
    args = None
    deps = None

    if not('type' in objdesc):
        return objdesc

    obj_type = objdesc['type']

    if 'args' in objdesc:
        args = objdesc['args']

    if 'deps' in objdesc:
        for key, value in objdesc['deps'].items():
            if type(value) == list:
                depobj = []
                for element in value:
                    if element in services:
                        depobj.append(services[element])
                    else:
                        depobj.append(create_instance(element, conf, services, spawn_fn))
            else:
                if value in services:
                    depobj = services[value]
                else:
                    depobj = create_instance(value, conf, services, spawn_fn)

            if not deps:
                deps = {}

            deps[key] = depobj

    if args and deps:
        args.update(deps)
    elif deps:
        assert not args and len(deps.keys()) > 0
        args = deps

#    logger.debug("creating object of type = ", obj_type)
    newobj = spawn_fn(obj_type, args)
    if hasattr(newobj, '__dict__'):
        #print("Instance name = ", instance_name)
        newobj.__dict__['gestalt_name'] = instance_name

    assert newobj
    return newobj


def construct_services(conf, create_fn):
    services = {}
    level = 0
    max_level = 0

    while level <= max_level:
        pop_keys = set([])
        for key, value in conf.items():
 #           print ("VALUE = ", value)
            if not ('service' in value) or not value['service']:
                continue

            level_value = 0
            if 'service-level' in value:
                level_value = value['service-level']

            if level_value > max_level:
                max_level = level_value

            if level_value <= level:
                services[key] = create_fn(key, conf, services)
                pop_keys.add(key)

        for key in pop_keys:
            conf.pop(key)

        level += 1

    return services


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


        conf.pop('includes')
    return ret


def construct_application(conf, create_fn=create_instance):
    application = {'main': None}

    includes = load_includes(conf)

    assert len(set(conf.keys()).intersection(includes.keys())) == 0

    conf.update(includes)
    services = construct_services(conf, create_fn)
#    logger.debug("conf keys = ", conf.keys())

    for key, value in conf.items():
        if 'main' in conf[key]:
            application['main'] = create_fn(key, conf, services)

    application['services'] = services
    #print("APPLICATION = ", application)
    assert application['main']
    return application


