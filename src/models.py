from pydantic import BaseModel


class VerifyModel(BaseModel):
    request: dict
    vk_token: str


class OperationResult(BaseModel):
    result: str


class GroupAddModel(BaseModel):
    group_id: int
    texts: list[str]
    vk_token: str


class GroupAndStatusModel(BaseModel):
    group_id: int
    group_status: int


class GroupAndStatusModelList(BaseModel):
    data: list[GroupAndStatusModel]


class DataDict(BaseModel):
    data: dict


class GenerateModel(BaseModel):
    microservice_host_name: str
    hint: str
