import logging
from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from utils import is_valid
from config import Config
from database import Database, DBException
from microservices import MicroserviceManager, MicroserviceException
from models import VerifyModel, OperationResult, GroupAddModel, GroupAndStatusModelList, DataString, GenerateQueryModel, GroupAndStatusModel, RenewModel


logging.basicConfig(format="%(asctime)s %(message)s", handlers=[logging.FileHandler(
    "/home/logs/log.txt", mode="w")], datefmt="%I:%M:%S %p", level=logging.INFO)


conf = Config("/home/config.json")
app = FastAPI()
db = Database(conf.db_user, conf.db_password,
              conf.db_db, conf.db_port, conf.db_host)
mmgr = MicroserviceManager(conf.services)

origins = [
    "https://localhost:10888",
    "https://user133207816-tmrqowmv.wormhole.vk-apps.com",
    "https://localhost:14565",
    "http://localhost:14565",
    "https://localhost",
    "http://localhost",
    "https://vk.com",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DESCRIPTION = """
Сервис, генерирующий контент для социальной сети ВКонтакте
"""


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Strawberry",
        version="0.1.0",
        description=DESCRIPTION,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.on_event("startup")
def startup():
    '''При старте сервера проверить, все ли таблицы на месте и если нет, то создать'''
    logging.info("Server started")
    try:
        if not db.tables_exist():
            logging.info("Creating tables...")
            db.migrate()
            logging.info("Creating tables...\tOK")
    except DBException as exc:
        logging.info(
            "Cannot connect to database, maybe it is still booting...")
        raise Exception(
            "Rebooting and hoping database will be online...") from exc


@app.on_event("startup")
@repeat_every(seconds=60)
async def check_statuses():
    '''Автоматическое удаление старых токенов и обновление статусов пабликов'''
    try:
        logging.info("Updating groups statuses...")
        groups = db.get_all_groups()
        for group in groups:
            if mmgr.check_status(group.group_id):
                db.update_group_status(group.group_id, 0)
            else:
                db.update_group_status(group.group_id, 3)
        logging.info("Updating groups statuses...\tOK")
    except DBException as exc:
        logging.error(f"DB ERROR: {exc}")
    except MicroserviceException as exc:
        logging.error(f"MICROSERVICE ERROR: {exc}")
    except Exception as exc:
        logging.error(f"ERROR: {exc}")


@app.post("/verify", response_model=OperationResult)
async def verify(data: VerifyModel):
    '''Добавляет токен в базу данных'''
    query_dict = data.request
    vk_token = data.vk_token
    logging.info("/verify")
    try:
        if is_valid(query=query_dict, secret=conf.client_secret):
            db.add_token(vk_token)
            logging.info("/verify OK")
            return OperationResult(status=0)
        logging.error("/verify bad query")
        return OperationResult(status=1)
    except DBException as exc:
        logging.error(f"DB ERROR: {exc}")
        return OperationResult(status=5)
    except Exception as exc:
        logging.error(f"ERROR: {exc}")
        return OperationResult(status=2)


@app.post("/renew", response_model=OperationResult)
async def renew(data: RenewModel):
    '''Заменяет старый токен на новый'''
    old_vk_token = data.old_vk_token
    new_vk_token = data.new_vk_token
    logging.info("/renew")
    try:
        if not db.is_valid_token(old_vk_token):
            logging.error("/renew bad old token")
            return OperationResult(status=1)
        db.update_token(old_vk_token, new_vk_token)
        logging.info("/renew OK")
        return OperationResult(status=0)
    except DBException as exc:
        logging.error(f"DB ERROR: {exc}")
        return OperationResult(status=5)
    except Exception as exc:
        logging.error(f"ERROR: {exc}")
        return OperationResult(status=2)


@app.post("/add_group", response_model=OperationResult)
async def add_group(data: GroupAddModel):
    '''Добавляет айди группы в базу данных и отправляет массив текстов постов этой группы'''
    group_id = data.group_id
    texts = data.texts
    vk_token = data.vk_token
    logging.info("/add_group")
    try:
        if not db.is_valid_token(vk_token):
            logging.error("/add_group bad token")
            return OperationResult(status=1)
        db.add_group(group_id, vk_token)
        mmgr.add_group(group_id, texts)
        logging.info("/add_group OK")
        return OperationResult(status=0)
    except MicroserviceException as exc:
        logging.error(f"MICROSERVICE ERROR: {exc}")
        return OperationResult(status=4)
    except DBException as exc:
        logging.error(f"DB ERROR: {exc}")
        return OperationResult(status=5)
    except Exception as exc:
        logging.error(f"ERROR: {exc}")
        return OperationResult(status=2)


@app.get("/get_groups", response_model=GroupAndStatusModelList)
async def get_groups(vk_token: str, group_id: int = None, offset: int = None, count: int = None):
    '''Возвращает массив пар айди группы : статус'''
    logging.info("/get_groups")
    try:
        if not db.is_valid_token(vk_token):
            logging.error("/get_groups bad token")
            return GroupAndStatusModelList(status=1, data=[], count=0)
    except DBException as exc:
        logging.error(f"DB ERROR: {exc}")
        return GroupAndStatusModelList(status=5, data=[], count=0)
    if not group_id is None:
        try:
            result = db.get_group_status(group_id)
            logging.info("/get_groups OK")
            return GroupAndStatusModelList(status=0, data=[GroupAndStatusModel(group_id=group_id, group_status=result)], count=1)
        except DBException as exc:
            logging.error(f"DB ERROR: {exc}")
            return GroupAndStatusModelList(status=5, data=[], count=0)
        except Exception as exc:
            logging.error(f"ERROR: {exc}")
            return GroupAndStatusModelList(status=2, data=[], count=0)
    else:
        try:
            result = db.get_owned_groups(vk_token)
            total_len = len(result)
            if (not offset is None) and (not count is None):
                result = result[offset:offset+count]
                logging.info("/get_groups OK")
            return GroupAndStatusModelList(status=0, data=result, count=total_len)
        except DBException as exc:
            logging.error(f"DB ERROR: {exc}")
            return GroupAndStatusModelList(status=5, data=[], count=0)
        except Exception as exc:
            logging.error(f"ERROR: {exc}")
            return GroupAndStatusModelList(status=2, data=[], count=0)


@app.post("/generate_text", response_model=DataString)
async def generate_text(data: GenerateQueryModel):
    '''Генерирует текст по описанию hint'''
    group_id = data.group_id
    vk_token = data.vk_token
    hint = data.hint
    logging.info("/generate_text")
    try:
        if not db.is_valid_token(vk_token):
            logging.info("/generate_text bad token")
            return DataString(data="", status=1)
    except DBException as exc:
        logging.error(f"DB ERROR: {exc}")
        return DataString(data="", status=5)

    try:
        group_status = db.get_group_status(group_id)
        if group_status == 0:
            result = mmgr.generate("text_gen", group_id, hint)
            logging.info("/generate_text OK")
            return DataString(data=result, status=0)
        logging.error("/generate_text group not ready")
        return DataString(data="", status=3)
    except MicroserviceException as exc:
        logging.error(f"MICROSERVICE ERROR: {exc}")
        return DataString(data="", status=4)
    except DBException as exc:
        logging.error(f"DB ERROR: {exc}")
        return DataString(data="", status=5)
    except Exception as exc:
        logging.error(f"ERROR: {exc}")
        return DataString(data="", status=2)
