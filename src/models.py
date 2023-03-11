from pydantic import BaseModel
from fastapi import Response


class VerifyModel(BaseModel):
    request: dict
    vk_token: str


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


class DataString(BaseModel):
    data: str
    status: int

class GenerateModel(BaseModel):
    microservice_host_name: str
    hint: str
