# FastAPI — Швидкий старт

## Що таке FastAPI?

FastAPI — це сучасний, швидкий веб-фреймворк для створення API на Python 3.7+, заснований на стандартних анотаціях типів Python.

## Переваги FastAPI

- **Швидкість**: Один з найшвидших Python фреймворків (завдяки Starlette та Pydantic)
- **Автоматична документація**: Swagger UI та ReDoc з коробки
- **Валідація**: Автоматична валідація даних через Pydantic
- **Type hints**: Повна підтримка type hints
- **Async/Await**: Нативна підтримка асинхронного коду

## Встановлення

```bash
pip install fastapi
pip install "uvicorn[standard]"
```

## Простий приклад

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
```

Запуск:

```bash
uvicorn main:app --reload
```

## Pydantic моделі

Використовуйте Pydantic для валідації та серіалізації даних:

```python
from pydantic import BaseModel
from typing import Optional

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

@app.post("/items/")
async def create_item(item: Item):
    return item
```

## Path параметри з валідацією

```python
from fastapi import Path

@app.get("/items/{item_id}")
async def read_item(
    item_id: int = Path(..., title="The ID of the item", ge=1),
):
    return {"item_id": item_id}
```

## Query параметри

```python
from typing import Optional

@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}
```

## Request Body

```python
from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None

@app.post("/users/")
async def create_user(user: User):
    return user
```

## Обробка помилок

```python
from fastapi import HTTPException

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]
```

## Залежності (Dependency Injection)

```python
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/")
async def read_users(db: Session = Depends(get_db)):
    return db.query(User).all()
```

## Аутентифікація з JWT

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect credentials")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    return get_current_user(token)
```

## CORS налаштування

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Background Tasks

```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    # Send email logic
    pass

@app.post("/send-notification/")
async def send_notification(
    email: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(send_email, email, "Welcome!")
    return {"message": "Notification sent"}
```

## WebSockets

```python
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message: {data}")
```

## Тестування

```python
from fastapi.testclient import TestClient

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
```

## Deployment

Для production використовуйте Gunicorn з Uvicorn workers:

```bash
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Структура проекту

```
myapp/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   ├── database.py
│   └── routers/
│       ├── __init__.py
│       ├── users.py
│       └── items.py
├── tests/
│   └── test_main.py
├── requirements.txt
└── README.md
```

## Висновок

FastAPI — це потужний та сучасний фреймворк для створення API. Він поєднує швидкість, простоту використання та автоматичну документацію.
