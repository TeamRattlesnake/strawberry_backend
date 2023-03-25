import logging
import json
import time
from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from utils import is_valid
from config import Config
from database import Database, DBException
from microservices import MicroserviceManager, MicroserviceException
from models import OperationResult, GroupAddModel, GroupAndStatusModel, GroupAndStatusModelList, DataString, GenerateQueryModel


logging.basicConfig(format="%(asctime)s %(message)s", handlers=[logging.FileHandler(
    f"/home/logs/server_{time.ctime()}.txt", mode="w", encoding="UTF-8")], datefmt="%I:%M:%S %p", level=logging.INFO)


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
Выпускной проект ОЦ VK в МГТУ команды Team Rattlesnake. Сервис, генерирующий контент для социальной сети ВКонтакте. Посты генерируются сами с помощью нейросетей. Станьте популярным в сети с помощью Strawberry!

* Коленков Андрей - Team Lead, Backend Python Dev 🍓
* Роман Медников - Frontend React Dev 🍓
* Василий Ермаков - Data Scientist 🍓

"""


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Strawberry🍓",
        version="0.1.0",
        description=DESCRIPTION,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

def add_user(vk_user_id):
    '''Добавляет vk_user_id в базу данных'''
    try:
        db.add_user_id(vk_user_id)
        return True
    except DBException:
        return False
    except Exception:
        return False

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
            "Cannot connect to database, maybe it is still booting... REBOOT NOW!")
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
                logging.error(f"group: {group.group_id};\tstatus: READY")
                db.update_group_status(group.group_id, 0)
            else:
                logging.error(f"group: {group.group_id};\tstatus: NOT READY")
                db.update_group_status(group.group_id, 1)
        logging.info("Updating groups statuses...\tOK")
    except DBException as exc:
        logging.error(f"DB ERROR: {exc}")
    except MicroserviceException as exc:
        logging.error(f"MICROSERVICE ERROR: {exc}")
    except Exception as exc:
        logging.error(f"ERROR: {exc}")


@app.post("/add_group", response_model=OperationResult)
async def add_group(data: GroupAddModel):
    '''Добавляет айди группы в базу данных и отправляет массив текстов постов этой группы'''
    vk_params = data.vk_params
    group_id = data.group_id
    texts = data.texts
    vk_params_dict = json.loads(vk_params)
    user_id = vk_params_dict["vk_user_id"]

    logging.info(
        f"POST /add_group\tPARAMS: vk_params={vk_params[:16]}..., len_texts={len(texts)}, group_id={group_id}")
    try:
        if not is_valid(query=vk_params_dict, secret=conf.client_secret):
            logging.error("/add_group query is not valid")
            return OperationResult(status=1)
        db.add_group(group_id, user_id)
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
async def get_groups(vk_params: str, group_id: int = None, offset: int = None, count: int = None):
    '''Возвращает массив пар айди группы : статус'''
    vk_params_dict = json.loads(vk_params)
    vk_user_id = vk_params_dict["vk_user_id"]

    logging.info(
        f"GET /get_groups\tPARAMS: vk_params={vk_params[:16]}..., group_id={group_id}, offset={offset}, count={count}")
    if not is_valid(query=vk_params_dict, secret=conf.client_secret):
        logging.error("/get_groups query is not valid")
        return GroupAndStatusModelList(status=1, data=[], count=0)
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
            result = db.get_owned_groups(vk_user_id)
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

    vk_params = data.vk_params
    vk_params_dict = json.loads(vk_params)
    group_id = data.group_id
    hint = data.hint
    logging.info(
        f"POST /generate_text\tPARAMS: vk_params={vk_params[:16]}..., group_id={group_id}, hint={hint}")

    if is_valid(query=vk_params_dict, secret=conf.client_secret):
        logging.info("/generate_text query is not valid")
        return DataString(data="", status=1)

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
