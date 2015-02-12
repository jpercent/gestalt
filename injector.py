
__author__ = 'jpercent'


class DependencyInjector(object):
    def __init__(self, factory=None):
        super(DependencyInjector, self).__init__()
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

