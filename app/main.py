from datetime import datetime
from enum import Enum
from typing import Annotated

from fastapi import FastAPI, Form, UploadFile
from pydantic import BaseModel

app = FastAPI()


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


class User(BaseModel):
    id: int
    name: str = "John Doe"
    created_at: datetime | None = None
    friends: list[int] = []


external_data = {
    "id": "123",
    'name': 'Junior Developer',
    "created_at": "2017-06-01 12:22",
    "friends": [1, "2", b"3"],
}


@app.get('/')
async def home():
    user = User(**external_data)
    return {"user": user}


@app.get('/test')
async def test(name: str | None = None, page: int | None = None):
    if name is not None:
        return {"message": f"welcome {name}!"}

    if page is not None:
        return {"message": f"this is page {page}!"}

    return {"message": f'welcome to test page!'}


@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip: skip + limit]


class FormData(BaseModel):
    username: str
    password: str | None = None

    model_config = {"extra": "forbid"}


@app.post("/login/")
async def login(data: Annotated[FormData, Form()]):
    return data


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    content = await file.read()
    size = len(content)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": size,
    }


@app.get("/items/{item_id}")
async def read_item(item_id: str, query: str | None = None):
    if query:
        return {"item_id": item_id, "query": query}
    return {"item_id": item_id}


@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}


@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}
