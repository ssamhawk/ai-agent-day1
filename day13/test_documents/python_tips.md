# Python Programming Tips

## Code Quality

### Type Hints

Use type hints to make your code more readable and catch errors early:

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

def add_numbers(a: int, b: int) -> int:
    return a + b
```

### Docstrings

Always document your functions with docstrings:

```python
def calculate_average(numbers: list[float]) -> float:
    """
    Calculate the average of a list of numbers.

    Args:
        numbers: A list of numerical values

    Returns:
        The arithmetic mean of the numbers

    Raises:
        ValueError: If the list is empty
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)
```

## Performance Tips

### List Comprehensions

List comprehensions are faster and more Pythonic:

```python
# Slow
squares = []
for i in range(10):
    squares.append(i ** 2)

# Fast
squares = [i ** 2 for i in range(10)]
```

### Use Built-in Functions

Built-in functions are optimized in C and much faster:

```python
# Slow
total = 0
for num in numbers:
    total += num

# Fast
total = sum(numbers)
```

## Error Handling

Always use specific exceptions:

```python
try:
    result = divide(a, b)
except ZeroDivisionError:
    print("Cannot divide by zero")
except TypeError:
    print("Invalid types for division")
```

## Context Managers

Use context managers for resource management:

```python
with open('file.txt', 'r') as f:
    content = f.read()
```

## Modern Python Features

### F-strings

F-strings are the best way to format strings:

```python
name = "Alice"
age = 30
print(f"{name} is {age} years old")
```

### Dataclasses

Use dataclasses for simple data structures:

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int
    email: str
```

### Match Statements (Python 3.10+)

Pattern matching makes code cleaner:

```python
match status_code:
    case 200:
        return "Success"
    case 404:
        return "Not Found"
    case 500:
        return "Server Error"
```
