import importlib

__author__ = 'jpercent'


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

