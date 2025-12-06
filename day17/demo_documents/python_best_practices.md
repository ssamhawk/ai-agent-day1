# Python Best Practices для професіоналів

## Якість коду

### Type Hints

Використовуйте анотації типів для кращої читабельності та виявлення помилок:

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

def calculate_sum(numbers: list[int]) -> int:
    return sum(numbers)

from typing import Optional, Union, Dict, List

def process_data(
    data: Dict[str, any],
    optional_param: Optional[str] = None
) -> List[str]:
    results: List[str] = []
    # Processing logic
    return results
```

### Docstrings

Завжди документуйте свої функції:

```python
def calculate_average(numbers: list[float]) -> float:
    """
    Обчислює середнє арифметичне списку чисел.

    Args:
        numbers: Список числових значень

    Returns:
        Середнє арифметичне чисел

    Raises:
        ValueError: Якщо список порожній

    Examples:
        >>> calculate_average([1, 2, 3, 4, 5])
        3.0
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)
```

## Performance оптимізації

### List Comprehensions

List comprehensions швидші та більш Pythonic:

```python
# Повільно
squares = []
for i in range(10):
    squares.append(i ** 2)

# Швидко
squares = [i ** 2 for i in range(10)]

# З умовою
even_squares = [i ** 2 for i in range(10) if i % 2 == 0]
```

### Generator Expressions

Для великих даних використовуйте генератори:

```python
# Споживає багато пам'яті
sum([i ** 2 for i in range(1000000)])

# Ефективно
sum(i ** 2 for i in range(1000000))
```

### Built-in функції

Вбудовані функції оптимізовані в C:

```python
# Повільно
total = 0
for num in numbers:
    total += num

# Швидко
total = sum(numbers)

# Пошук максимуму
max_value = max(numbers)

# Фільтрація
evens = list(filter(lambda x: x % 2 == 0, numbers))
```

## Обробка помилок

### Специфічні винятки

```python
# Погано
try:
    result = divide(a, b)
except:
    print("Error")

# Добре
try:
    result = divide(a, b)
except ZeroDivisionError:
    logger.error("Division by zero")
    result = None
except TypeError:
    logger.error("Invalid types for division")
    result = None
```

### Context Managers

```python
# Автоматичне закриття файлу
with open('file.txt', 'r') as f:
    content = f.read()

# Custom context manager
from contextlib import contextmanager

@contextmanager
def database_connection():
    conn = connect_to_db()
    try:
        yield conn
    finally:
        conn.close()

with database_connection() as conn:
    conn.execute("SELECT * FROM users")
```

## Сучасні Python фічі

### F-strings (Python 3.6+)

```python
name = "Alice"
age = 30

# Старий спосіб
print("Name: %s, Age: %d" % (name, age))

# Добре
print(f"{name} is {age} years old")

# З форматуванням
price = 19.99
print(f"Price: ${price:.2f}")

# З виразами
print(f"Next year: {age + 1}")
```

### Dataclasses (Python 3.7+)

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Person:
    name: str
    age: int
    email: str
    hobbies: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.age < 0:
            raise ValueError("Age cannot be negative")

person = Person("Alice", 30, "alice@example.com")
```

### Pattern Matching (Python 3.10+)

```python
def handle_response(status_code: int) -> str:
    match status_code:
        case 200:
            return "Success"
        case 404:
            return "Not Found"
        case 500 | 502 | 503:
            return "Server Error"
        case _:
            return "Unknown Status"
```

### Walrus Operator (Python 3.8+)

```python
# Без walrus
data = fetch_data()
if data:
    process(data)

# З walrus
if data := fetch_data():
    process(data)

# В циклі
while (line := file.readline()) != '':
    process(line)
```

## Async/Await

```python
import asyncio
import aiohttp

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()

async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)

# Запуск
urls = ["http://example.com", "http://example.org"]
results = asyncio.run(fetch_all(urls))
```

## Testing

### Pytest

```python
import pytest

def test_addition():
    assert 1 + 1 == 2

def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        1 / 0

@pytest.fixture
def sample_data():
    return {"name": "Alice", "age": 30}

def test_with_fixture(sample_data):
    assert sample_data["name"] == "Alice"

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert input * 2 == expected
```

## Code Style

### PEP 8

```python
# Хороші імена
user_count = 10
is_valid = True
MAX_CONNECTIONS = 100

# Погані імена
x = 10
flag = True
max = 100

# Функції - lowercase з підкресленнями
def calculate_total_price():
    pass

# Класи - CamelCase
class UserManager:
    pass

# Константи - UPPERCASE
API_KEY = "secret"
```

### Imports

```python
# Порядок imports
import os
import sys

from typing import List, Dict

import numpy as np
import pandas as pd

from myapp.models import User
from myapp.utils import helper
```

## Logging

```python
import logging

# Налаштування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Використання
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")

# З exception
try:
    risky_operation()
except Exception as e:
    logger.exception("Operation failed")
```

## Висновок

Ці best practices допоможуть писати чистіший, швидший та надійніший Python код. Завжди слідуйте PEP 8, використовуйте type hints та пишіть тести!
