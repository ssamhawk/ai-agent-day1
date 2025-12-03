# Docker для Python розробників

## Що таке Docker?

Docker — це платформа для розробки, доставки та запуску додатків у контейнерах. Контейнери дозволяють упакувати додаток разом з усіма його залежностями в стандартизовану одиницю.

## Чому варто використовувати Docker?

- **Консистентність**: Однакове середовище на dev, test та prod
- **Ізоляція**: Кожен додаток працює у своєму контейнері
- **Портативність**: Контейнери можуть працювати на будь-якій системі
- **Ефективність**: Контейнери діляться ядром ОС, що робить їх легкими

## Створення Dockerfile для Python

Dockerfile — це текстовий файл з інструкціями для створення Docker образу:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
```

## Побудова образу

Щоб створити Docker образ, виконайте:

```bash
docker build -t myapp .
```

Ця команда створить образ з тегом "myapp", використовуючи Dockerfile з поточної директорії.

## Запуск контейнера

Після створення образу, запустіть контейнер:

```bash
docker run -p 8000:8000 myapp
```

Це проектує порт 8000 контейнера на порт 8000 вашої машини.

## Docker Compose для мультисервісних додатків

Для додатків з кількома сервісами використовуйте Docker Compose:

```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://db:5432/mydb

  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=secret
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

Запуск:

```bash
docker-compose up
```

## Best Practices

1. **Використовуйте конкретні версії**: Замість `python:latest` використовуйте `python:3.11-slim`
2. **Мінімізуйте шари**: Об'єднуйте RUN команди коли можливо
3. **Використовуйте .dockerignore**: Виключайте непотрібні файли
4. **Не запускайте як root**: Створіть non-root користувача
5. **Multi-stage builds**: Зменшіть розмір фінального образу

## Приклад .dockerignore

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.git
.gitignore
.dockerignore
Dockerfile
docker-compose.yml
README.md
tests/
```

## Оптимізація образу

Використовуйте multi-stage build для зменшення розміру:

```dockerfile
# Builder stage
FROM python:3.11 as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH

CMD ["python", "app.py"]
```

## Корисні команди

```bash
# Список контейнерів
docker ps

# Зупинити контейнер
docker stop <container_id>

# Видалити образ
docker rmi <image_name>

# Очистити невикористані ресурси
docker system prune -a

# Подивитися логи
docker logs <container_id>

# Виконати команду в контейнері
docker exec -it <container_id> bash
```

## Debugging

Для debugging увійдіть в контейнер:

```bash
docker run -it myapp /bin/bash
```

Або підключіться до запущеного контейнера:

```bash
docker exec -it <container_id> /bin/bash
```

## Висновок

Docker спрощує розгортання та забезпечує консистентність середовищ. Почніть з простих контейнерів і поступово переходьте до більш складних налаштувань.
