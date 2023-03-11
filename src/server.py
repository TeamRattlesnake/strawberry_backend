import logging
from fastapi.openapi.utils import get_openapi
from fastapi import Response
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from utils import is_valid
from config import EnvironmentConfig
from database import Database
from models import VerifyModel, OperationResult, GroupAddModel, GroupAndStatusModel, GroupAndStatusModelList, DataString
from microservices import microservice_add_model, microservice_generate, microservice_check_status


logging.basicConfig(format="%(asctime)s %(message)s",
                    datefmt="%I:%M:%S %p", level=logging.INFO)

conf = EnvironmentConfig()
app = FastAPI()
db = Database(conf.MYSQL_USER, conf.MYSQL_PASSWORD,
              conf.MYSQL_DATABASE, conf.MYSQL_TCP_PORT, conf.MYSQL_HOST)

origins = [
    "https://localhost:10888",
    "https://user133207816-tmrqowmv.wormhole.vk-apps.com",
    "https://localhost:14565",
    "http://localhost:14565",
    "https://localhost",
    "http://localhost",
    "https://vk.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Strawberry",
        version="0.0.2",
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
    '''При старте сервера проверить, все ли таблицы на месте и если нет, то создать'''
    if not db.tables_exist():
        db.migrate()


@app.on_event("startup")
@repeat_every(seconds=60)
async def check_statuses():
    '''Автоматическое удаление старых токенов и обновление статусов пабликов'''
    db.autoremove_old_tokens()
    groups = db.get_all_groups_status()
    for group in groups:
        count = 0
        wanted_count = len(conf.MICROSERVICES_HOST_NAMES)
        for microservice_host_name in conf.MICROSERVICES_HOST_NAMES:
            status = microservice_check_status(
                group.group_id, microservice_host_name)
            count += status
        if count == wanted_count:
            db.update_group_status(group.group_id, 0)


@app.post("/verify", response_model=OperationResult)
async def verify(data: VerifyModel):
    '''Добавляет токен в базу данных'''
    query_dict = data.request
    vk_token = data.vk_token
    if is_valid(query=query_dict, secret=conf.CLIENT_SECRET):
        try:
            db.add_token(vk_token)
            return OperationResult(custom_code=0)
        except:
            return OperationResult(custom_code=2)


@app.post("/add_group", response_model=OperationResult)
async def add_group(data: GroupAddModel):
    '''Добавляет айди группы в базу данных и отправляет массив текстов постов этой группы'''
    group_id = data.group_id
    texts = data.texts
    vk_token = data.vk_token
    if not db.is_valid_token(vk_token):
        return OperationResult(custom_code=1)
    try:
        db.add_group(group_id)
        for microservice_host_name in conf.MICROSERVICES_HOST_NAMES:
            microservice_add_model(microservice_host_name, group_id, texts)
        return OperationResult(custom_code=0)
    except:
        return OperationResult(custom_code=2)


@app.get("/get_groups", response_model=GroupAndStatusModelList)
async def get_groups(vk_token: str):
    '''Возвращает массив пар айди группы : статус'''
    if not db.is_valid_token(vk_token):
        return GroupAndStatusModelList(custom_code=1, data=[])
    try:
        result = db.get_all_groups_status
        return GroupAndStatusModelList(custom_code=0, data=result)
    except:
        return GroupAndStatusModelList(custom_code=2, data=[])


@app.get("/generate_text", response_model=DataString)
async def generate_text(group_id: int, vk_token: str, hint: str = None):
    '''Генерирует текст по описанию hint'''
    if not db.is_valid_token(vk_token):
        return DataString(data="", custom_code=1)
    try:
        result = microservice_generate(group_id, "text_gen", hint)
        return DataString(data="", custom_code=0)
    except:
        return DataString(data="", custom_code=2)


@app.get("/image_get", response_model=DataString)
async def image_gen(group_id: int, vk_token: str, hint: str = None):
    '''Генерирует картинку по описанию hint и отправляет ссылку на нее'''
    if not db.is_valid_token(vk_token):
        return DataString(data="", custom_code=1)
    try:
        result = microservice_generate(group_id, "image_get", hint)
        return DataString(data="", custom_code=0)
    except:
        return DataString(data="", custom_code=2)


@app.get("/generate_meme_template", response_model=DataString)
async def generate_meme_template(group_id: int, vk_token: str, hint: str = None):
    '''Ищет шаблон мема по описанию hint и отправляет ссылку на нее'''
    if not db.is_valid_token(vk_token):
        return DataString(data="", custom_code=1)
    try:
        result = microservice_generate(group_id, "meme_template_gen", hint)
        return DataString(data="", custom_code=0)
    except:
        return DataString(data="", custom_code=2)
