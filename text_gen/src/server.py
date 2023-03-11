import copy
import os
import logging
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from models import GroupAddModel, Data, GroupStatusModel

import neural_network

logging.basicConfig(format="%(asctime)s %(message)s",
                    datefmt="%I:%M:%S %p", level=logging.INFO)

app = FastAPI()


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Strawberry Mircoservice",
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
nn = None

@app.on_event("startup")
def startup():
    if not os.path.exists("weights"):
        os.makedirs("weights")
    if not os.path.exists("train_test_datasets"):
        os.makedirs("train_test_datasets")
    global nn
    nn = neural_network.NeuralNetwork()


def is_model_ready(group_id: int) -> bool:
    return os.path.exists(f"weights/trained-{group_id}.pt")


@app.post("/add_group")
async def add_group(data: GroupAddModel):
    group_id = data.group_id
    texts = data.texts
    if is_model_ready(group_id):
        return
    tmp_nn = copy.deepcopy(nn)
    tmp_nn.group_id = group_id
    train_dataset_path = f"train_test_datasets/train{group_id}"
    test_dataset_path = f"train_test_datasets/test{group_id}"
    train_texts = texts[int(len(texts)*0.1):]
    test_texts = texts[:int(len(texts)*0.1)]
    tmp_nn.build_text_file(train_texts, train_dataset_path)
    tmp_nn.build_text_file(test_texts, test_dataset_path)
    tmp_nn.load_dataset(train_dataset_path, test_dataset_path)
    tmp_nn.train(f"weights/{group_id}.pt")
    os.rename(f"weights/{group_id}.pt", f"weights/trained-{group_id}.pt")


@app.get("/generate", response_model=Data)
async def generate(group_id: int, hint: str):
    if not is_model_ready(group_id):
        return Data(data="")
    tmp_nn = neural_network.NeuralGenerator(f"weights/trained-{group_id}.pt")
    result_post = tmp_nn.generate(hint)
    return Data(data=result_post)


@app.get("/check_status", response_model=GroupStatusModel)
async def check_status(group_id: int):
    if is_model_ready(group_id):
        return GroupStatusModel(result=1)
    return GroupStatusModel(result=0)
