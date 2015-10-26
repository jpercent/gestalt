import jestalt
import sys


class Hello(jestalt.Application):
    def __init__(self, message_manager=None, io_service=None):
        self.message_manager = message_manager
        self.io_service = io_service

    def run(self):
        messages = set()
        while True:
            next = self.message_manager.get_next()
            if not(next in messages):
                self.io_service.output(next)
                messages.add(next)
            else:
                break


class Messages(object):
    def __init__(self, messages=None):
        self.messages = messages
        self.cursor = 0

    def get_next(self):
        if len(self.messages) > 0:
            ret = self.messages[self.cursor]
            self.cursor += 1
            if self.cursor >= len(self.messages):
                self.cursor = 0
            return ret
        else:
            raise Exception("No messages")


class FileOutput(object):
    def __init__(self, name=None, filename=None):
        self.name = name
        assert filename
        self.filename = filename

    def output(self, message):
        with open(self.filename, 'a') as fd:
            fd.write(message+'\n')


class StandardOutput(object):
    def __init__(self, name=None):
        self.name = name

    def output(self, message):
        print(message)


class MasterOutputService(object):
    def __init__(self, name=None, slaves=[]):
        self.name = name
        self.slaves = slaves

    def output(self, message):
        for slave in self.slaves:
            slave.output(message)


if __name__ == '__main__':
    options, args = jestalt.parse_options()
    app = jestalt.create(**vars(options))
    app['main'].run()
    sys.exit(0)
