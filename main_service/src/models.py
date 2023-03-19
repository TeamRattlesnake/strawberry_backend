from pydantic import BaseModel


class VerifyModel(BaseModel):
    request: dict
    vk_token: str


class RenewModel(BaseModel):
    old_vk_token: str
    new_vk_token: str


class OperationResult(BaseModel):
    """# Return codes:
     * 0 - ok
     * 1 - token error
     * 2 - unknown internal exception error
     * 3 - neural network is not ready
     * 4 - microservice error
     * 5 - db error
    """
    status: int


class GroupAddModel(BaseModel):
    group_id: int
    texts: list[str]
    vk_token: str


class GroupAndStatusModel(BaseModel):
    """# Return codes:
     * 0 - ok
     * 1 - token error
     * 2 - unknown internal exception error
     * 3 - neural network is not ready
     * 4 - microservice error
     * 5 - db error
    """
    group_id: int
    group_status: int


class GroupAndStatusModelList(BaseModel):
    """# Return codes:
     * 0 - ok
     * 1 - token error
     * 2 - unknown internal exception error
     * 3 - neural network is not ready
     * 4 - microservice error
     * 5 - db error
    """
    status: int
    data: list[GroupAndStatusModel]
    count: int


class DataString(BaseModel):
    """# Return codes:
     * 0 - ok
     * 1 - token error
     * 2 - unknown internal exception error
     * 3 - neural network is not ready
     * 4 - microservice error
     * 5 - db error
    """
    data: str
    status: int


class GenerateQueryModel(BaseModel):
    group_id: int
    vk_token: str
    hint: str = None


class GenerateModel(BaseModel):
    microservice_host_name: str
    hint: str
