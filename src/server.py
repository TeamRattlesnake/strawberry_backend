import logging
from fastapi.openapi.utils import get_openapi
from config import EnvironmentConfig
from database import Database
from fastapi import FastAPI
from utils import is_valid
from models import VerifyModel, OperationResult, GroupAddModel, GroupAndStatusModel, GroupAndStatusModelList, DataDict
from microservices import microservice_add_model, microservice_generate


logging.basicConfig(format="%(asctime)s %(message)s",
                    datefmt="%I:%M:%S %p", level=logging.INFO)

conf = EnvironmentConfig()
app = FastAPI()
db = Database(conf.MYSQL_USER, conf.MYSQL_PASSWORD,
              conf.MYSQL_DATABASE, conf.MYSQL_TCP_PORT, conf.MYSQL_HOST)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Strawberry",
        version="0.0.1",
        description="Сервис, генерирующий контент для социальной сети ВКонтакте",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://ih1.redbubble.net/image.1419893148.7415/bg,f8f8f8-flat,750x,075,f-pad,750x1000,f8f8f8.jpg"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.on_event("startup")
def startup():
    if not db.tables_exist():
        db.migrate()


@app.post("/verify", response_model=OperationResult)
async def verify(data: VerifyModel):
    query_dict = data.request
    vk_token = data.vk_token
    if is_valid(query=query_dict, secret=conf.CLIENT_SECRET):
        db.add_token(vk_token)
        return OperationResult(result="Token added")
    return OperationResult(result="Token is fake")


@app.post("/add_group")
async def add_group(data: GroupAddModel):
    group_id = data.group_id
    texts = data.texts
    db.add_group(group_id)
    for microservice_host_name in conf.MICROSERVICES_HOST_NAMES:
        microservice_add_model(microservice_host_name, group_id, texts)


@app.get("/get_groups", response_model=GroupAndStatusModelList)
async def get_groups():
    result = db.get_all_groups_status
    return GroupAndStatusModelList(data=result)


@app.get("/generate", response_model=DataDict)
async def generate(group_id: int, microservice_host_name: str, hint: str = None):
    result = microservice_generate(group_id, microservice_host_name, hint)
    return DataDict(data=result)


@app.post("/update_group_status")
async def update_group_status(data: GroupAndStatusModel):
    group_id = data.group_id
    group_status = data.group_status
    db.update_group_status(group_id, group_status)
