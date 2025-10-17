
class Command:
    def __init__(self, id, name="", description=""):
        self.id = id
        self.name = name
        self.description = None
        self.args = {}

        # a function that takes the self.args as parameters
        self.exec = None
        self.undo = None

class Commands : 
    def __init__(self):
        self.commands = {}

    def add(self, command):
        self.commands[command.id] = command

    def create(self, id, exe=None, name="", description=""):
        c = Command(id, name, description)
        if exe:
            c.exec = exe
        self.add(c)
        return c

    #command could be a string or a Command if it's a string it's the id
    def exec(self, command, args=-1) : 
        if isinstance(command, str):
            command = self.commands[command]
        if (args == -1):
            args = command.args
        return command.exec(args)

    def has(self, id) : 
        return id in self.commands
