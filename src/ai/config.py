class Config:
    def __init__(self, port: int, name: str, machine: str = "127.0.0.1"):
        self.port = port
        self.name = name
        self.machine = machine
