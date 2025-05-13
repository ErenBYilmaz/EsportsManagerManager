from pydantic import BaseModel


class GameEventBase(BaseModel):
    def apply(self):
        raise NotImplementedError("Abstract method")

    def text_description(self):
        return self.short_notation()

    def short_notation(self):
        raise NotImplementedError("Abstract method")
