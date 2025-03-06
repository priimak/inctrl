from pyvisa import Resource


class CommandDispatcher:
    def __init__(self, visa_resource: Resource):
        self.visa_resource = visa_resource

    def read(self, msg: str) -> str:
        self.visa_resource.read(msg).strip()

    def write(self, msg: str, synchronize: bool = False) -> None:
        self.visa_resource.write(msg)
        if synchronize:
            self.sync()

    def query(self, msg: str) -> str:
        return self.visa_resource.query(msg).strip()

    def query_bytes(self, msg: str) -> bytes:
        return bytes(self.visa_resource.query_binary_values(msg, datatype = "B"))

    def sync(self) -> None:
        self.query("*OPC?")
