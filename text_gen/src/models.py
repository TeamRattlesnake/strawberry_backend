from pydantic import BaseModel


class GroupAddModel(BaseModel):
    group_id: int
    texts: list[str]


class Data(BaseModel):
    data: str


class GroupStatusModel(BaseModel):
    result: int  # 1 - Хорошо, 0 - Плохо
