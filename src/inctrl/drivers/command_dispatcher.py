from pyvisa import Resource


class CommandDispatcher:
    def __init__(self, visa_resource: Resource):
        self.visa_resource = visa_resource

    def read(self, msg: str) -> str:
        self.visa_resource.read(msg).strip()

    def write(self, msg: str) -> None:
        self.visa_resource.write(msg)

    def query(self, msg: str) -> str:
        return self.visa_resource.query(msg).strip()
