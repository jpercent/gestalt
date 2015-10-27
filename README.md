# Managing Python Dependencies with JSON

Jestalt is a framework for managing Python dependencies. Jestalt provides
a JSON-based interface for expressing how programs and services are created, 
connected and executed.

Systems with flat 
key/value configuration variables require software that manages how configuration 
values are propogated. By storing the configuration values in 
abstractions that model the system components, and following a few simple conventions, 
complex configurations can be stored and modified without writing and/or modifying software. 

## Getting started

### Installation

Before we can proceed to our example, we must install Jestalt. The easist way to install Jestalt
is to use *pip*. For more information about pip see [the pip documentation](https://pip.readthedocs.org/en/stable/).

After *pip* is installed, Jestalt can be installed by running the following command.

```
LOSX-JPERCENT:examples $ pip install jestalt
```

Now that Jestalt is installed we can work through the example. The example code can be 
found [here](https://github.com/jpercent/jestalt/example/)

### An example

To configure and connect objects as components of a system Jestalt needs to know some 
things about the system. 

For example, it needs to know the main entry point of the system. It supports the main 
value for indicating the main entry point - there *should* be only one of these, although 
no attempt to enforce this is made.

The main entry point must be a callable or support the *run()* method. What follows is 
an example hello world program using Jestalt. 

To follow along, you can place the following code into a file named *hello.py*.

```Python
class Hello(object):
    def run(self):
        print("Hello world")

```

The *Hello* object in the example above implements the *run* method. It is sufficient to 
 implement the *run* or *__callable__* method or be an actual callable - a function.
 
 It takes a little bit more infrastructure to run a Jestalt-based 
program. For starters, we need a JSON config. An example follows.

```JSON
{
"hello world": {
    "type": "hello.Hello",
    "main": true
  }
}
```

We've already disucssed the *main* keyword. Next notice the *type* value. This must
either be a factory method or the native constructor call. Note that it can be a function
that returns a function.

Now we need to invoke Jestalt on that configuration file. To do so, we can add the following
lines to the bottom of our *hello.py*.

```Python
options, args = jestalt.parse_options()
app = jestalt.create(**vars(options))
app['main'].run()
```

```
LOSX-JPERCENT:example $ ls
hello.json	hello.py
LOSX-JPERCENT:example $ python3 hello.py -c hello.json
Hello world
```

Let's build out our example to demonstrate a bit more of the 
functionality provided by Jestalt. Suppose we want to cycle through hello messages.
We could create an object as follows to perform these tasks.

```Python
class Hello(object):
    def __init__(self, message_manager=None):
        self.message_manager = message_manager

    def run(self):
        messages = set()
        while True:
            next = self.message_manager.get_next()
            if not(next in messages):
                print(next)
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
```

We've created an object that cycles through messages, which it receives as a parameter,
and we've created an argument to our *Hello* object that takes an object which has the
*get_next* method, which it uses to traverse messages. 

This is admittedly a bit contrived, but
we'll be able to use it to demonstrate a few interesting things.

To complete this example we must add the messages. We could hard code
them into the object, but instead we put them into JSON, as configuration data. This 
provides a nice separation of concerns. We've found keeping the configuration data 
separated from the code is highly advantageous.

```JSON
  "hello world": {
    "type": "hello.Hello",
    "main": true,
    "deps": {
      "message_manager": "messages"
    }
  },

  "messages": {
    "type": "hello.MessageService",
    "args": {
      "messages": [
        "Hello", "Happy", "Radiant", "World"
      ]
    }
  }
```

First thing to notice is the *"deps"* object embedded in the *"hello_world"* object. This
is a Jestalt keyword. The *"deps"* object indicates to Jestalt that the following key/value
is an object in the configuration space that should be created and injected into *hello_world* 
as keywork parameters.

If we look at *"messages"*, this object also has a new keyword. The *"args"* object. 
These values are turned into keyword arguments to the object being created.

The *args* keyword and the *deps* keyword parameters are combined as keyword parameters to 
the object being created. Running the updated as demonstrated above yields the following.

```
LOSX-JPERCENT:example $ python3 hello.py -c hello.json
Hello
Happy
Radiant
World
```

To build out this example even more, let's suppose we want to have an abstraction which
 handles the output. For example, we may want to have an output class that writes to standard out,
 and another that writes to a file. And we may want to have one that wraps many outputs such
 that messages can be written to standard out and to a file, and the combination of 
 output objects that are materialized can be managed via configuration.
 
 To do this we add the following code to our example.
 
 ```Python
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
        
 ```

We must also update the *Hello* class as follows.

```Python
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

```

Finally we update our configuration file.

```JSON
{
  "hello world": {
    "type": "hello.Hello",
    "main": true,
    "deps": {
      "message_manager": "messages",
      "io_service": "master_io_service"
    }
  },

  "messages": {
    "type": "hello.Messages",
    "args": {
      "messages": [
        "Hello", "Happy", "Radiant", "World"
      ]
    }
  },

  "file_output": {
    "type": "hello.FileOutput",
    "args": {
      "name": "file output",
      "filename": "example.log"
    }

  },

  "standard_output": {
    "type": "hello.StandardOutput",
    "args": {
      "name": "standard output"
    }
  },

  "master_io_service": {
    "type": "hello.MasterOutputService",
    "service": 0,
    "args": {
      "name": "Master IO Service"
    },

    "deps": {
      "slaves": ["standard_output", "file_output"]
    }
  }
}
```

Most of this just adds a bit of substance to the previous examples. There are 2 new features.
Firstly, note the *"master_io_service"* has both *deps* and *args*. Also, the 
*"master_io_service"* has a keyword that we've never seen before: *"service"*. 

The *service*
keyword indicates to Jestalt that this object is a singleton, so where ever it appears in the
config space, there should be only one created and all others should be references; a service is 
a singleton within the configuration space. Further,
the value of the *service* key indicates the level that it should be created at. This supports
creating a hierarchy of singleton dependencies.

Running the updated example yields the following. 
```
LOSX-JPERCENT:example $ python3 hello.py -c hello.json
Hello
Happy
Radiant
World
LOSX-JPERCENT:example $ cat example.log 
Hello
Happy
Radiant
World
```













