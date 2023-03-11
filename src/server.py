import logging
from fastapi.openapi.utils import get_openapi
from fastapi import Response
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from utils import is_valid
from config import EnvironmentConfig
from database import Database
from models import VerifyModel, OperationResult, GroupAddModel, GroupAndStatusModelList, DataString, GenerateQueryModel
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

description = """
Сервис, генерирующий контент для социальной сети ВКонтакте

## Return codes:
* 0 - ok
* 1 - token error
* 2 - internal exception error
* 3 - neural network is not ready

"""


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Strawberry",
        version="0.0.3",
        description=description,
        routes=app.routes,
    )
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
    try:
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
    except Exception as e:
        logging.info(f"{e}")


@app.post("/verify", response_model=OperationResult)
async def verify(data: VerifyModel):
    '''Добавляет токен в базу данных'''
    query_dict = data.request
    vk_token = data.vk_token
    if is_valid(query=query_dict, secret=conf.CLIENT_SECRET):
        try:
            db.add_token(vk_token)
            return OperationResult(status=0)
        except Exception as e:
            logging.info(f"{e}")
            return OperationResult(status=2)


@app.post("/add_group", response_model=OperationResult)
async def add_group(data: GroupAddModel):
    '''Добавляет айди группы в базу данных и отправляет массив текстов постов этой группы'''
    group_id = data.group_id
    texts = data.texts
    vk_token = data.vk_token
    if not db.is_valid_token(vk_token):
        return OperationResult(status=1)
    try:
        db.add_group(group_id)
        for microservice_host_name in conf.MICROSERVICES_HOST_NAMES:
            microservice_add_model(microservice_host_name, group_id, texts)
        return OperationResult(status=0)
    except Exception as e:
        logging.info(f"{e}")
        return OperationResult(status=2)


@app.get("/get_groups", response_model=GroupAndStatusModelList)
async def get_groups(vk_token: str, group_id: int = None, offset: int = None, count: int = None):
    '''Возвращает массив пар айди группы : статус'''
    if not db.is_valid_token(vk_token):
        return GroupAndStatusModelList(status=1, data=[], count=0)
    if not (group_id is None):
        try:
            result = db.get_group_status(group_id)
            return GroupAndStatusModelList(status=0, data=result, count=len(result))
        except Exception as e:
            logging.info(f"{e}")
            return GroupAndStatusModelList(status=2, data=[], count=0)
    else:
        try:
            result = db.get_all_groups_status()
            total_len = len(result)
            if (not offset is None) and (not count is None):
                result = result[offset:offset+count]
            return GroupAndStatusModelList(status=0, data=result, count=total_len)
        except Exception as e:
            logging.info(f"{e}")
            return GroupAndStatusModelList(status=2, data=[], count=0)


@app.post("/generate_text", response_model=DataString)
async def generate_text(data: GenerateQueryModel):
    '''Генерирует текст по описанию hint'''
    group_id = data.group_id
    vk_token = data.vk_token
    hint = data.hint
    if not db.is_valid_token(vk_token):
        return DataString(data="", status=1)
    try:
        group_status = db.get_group_status(group_id)
        if group_status == 0:
            #result = microservice_generate(group_id, "text_gen", hint)
            result = "Текстик"
            return DataString(data=result, status=0)
        return DataString(data="", status=3)
    except Exception as e:
        logging.info(f"{e}")
        return DataString(data="", status=2)


@app.post("/generate_image", response_model=DataString)
async def generate_image(data: GenerateQueryModel):
    '''Генерирует картинку по описанию hint и отправляет ссылку на нее'''
    group_id = data.group_id
    vk_token = data.vk_token
    hint = data.hint
    if not db.is_valid_token(vk_token):
        return DataString(data="", status=1)
    try:
        group_status = db.get_group_status(group_id)
        if group_status == 0:
            #result = microservice_generate(group_id, "image_gen", hint)
            result = "Текстик"
            return DataString(data=result, status=0)
        return DataString(data="", status=3)
    except Exception as e:
        logging.info(f"{e}")
        return DataString(data="", status=2)


@app.post("/generate_meme_template", response_model=DataString)
async def generate_meme_template(data: GenerateQueryModel):
    '''Ищет шаблон мема по описанию hint и отправляет ссылку на нее'''
    group_id = data.group_id
    vk_token = data.vk_token
    hint = data.hint
    if not db.is_valid_token(vk_token):
        return DataString(data="", status=1)
    try:
        group_status = db.get_group_status(group_id)
        if group_status == 0:
            #result = microservice_generate(group_id, "meme_template_gen", hint)
            result = "Текстик"
            return DataString(data=result, status=0)
        return DataString(data="", status=3)
    except Exception as e:
        logging.info(f"{e}")
        return DataString(data="", status=2)
