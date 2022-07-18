class Mode:
    def __init__(self, app):
        self.app = app
        self.frame = app.frame

    def start(self):
        self.frame.clear()

    def step(self):
        pass

    def receive(self, command, arg=None):
        pass

    def end(self):
        pass
