class ErrorMessage(RuntimeError):
    pass


class ConnectionErrorMessage(ErrorMessage):
    def __init__(self, title: str, msg: str):
        self.title = title
        self.msg = msg
