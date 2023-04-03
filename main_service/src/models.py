from pydantic import BaseModel


class OperationResult(BaseModel):
    """
    В status лежит статус операции
    status codes:
     * 0 - ok
     * 1 - token error
     * 2 - unknown internal exception error
     * 3 - neural network is not ready
     * 4 - microservice error
     * 5 - db error
    """
    status: int


class GroupAddModel(BaseModel):
    """Модель для добавления группы, принимается айди группы и список текстов"""
    group_id: int
    texts: list[str]


class GroupAndStatusModel(BaseModel):
    """
    Модель, содержащая айди групып и статус
    status codes:
     * 0 - group is ready
     * 1 - group is not ready
     * 2 - group is not in database
    """
    group_id: int
    group_status: int


class GroupAndStatusModelList(BaseModel):
    """
    Модель содержит в себе список GroupAndStatusModel и длину этого списка
    status codes:
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
    """
    Эта модель представляет собой пару - статус операции и информация в строке
    status codes:
     * 0 - ok
     * 1 - token error
     * 2 - unknown internal exception error
     * 3 - neural network is not ready
     * 4 - microservice error
     * 5 - db error
    """
    status: int
    data: str


class GenerateQueryModel(BaseModel):
    """Модель для генерации контента из нейросети. Принимает на вход имя сервиса, айди группы, для которой надо сгенерировать и подсказу/затравку"""
    service_name: str
    group_id: int
    hint: str
