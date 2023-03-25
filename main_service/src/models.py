from pydantic import BaseModel


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


class VerifyModel(BaseModel):
    vk_params: str
    vk_token: str


class GroupAddModel(BaseModel):
    vk_params: str
    group_id: int
    texts: list[str]


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
    vk_params: str
    group_id: int
    hint: str
