from pydantic import BaseModel


class VerifyModel(BaseModel):
    request: dict
    vk_token: str


class RenewModel(BaseModel):
    old_vk_token: str
    new_vk_token: str


class OperationResult(BaseModel):
    status: int


class GroupAddModel(BaseModel):
    group_id: int
    texts: list[str]
    vk_token: str


class GroupAndStatusModel(BaseModel):
    group_id: int
    group_status: int


class GroupAndStatusModelList(BaseModel):
    status: int
    data: list[GroupAndStatusModel]
    count: int


class DataString(BaseModel):
    data: str
    status: int


class GenerateQueryModel(BaseModel):
    group_id: int
    vk_token: str
    hint: str = None


class GenerateModel(BaseModel):
    microservice_host_name: str
    hint: str
