# Python Async Programming

## Introduction to Async/Await

Python's `async` and `await` keywords enable writing asynchronous code that can handle multiple tasks concurrently without using threads.

## Key Concepts

### Coroutines
A coroutine is a function defined with `async def`. It's a special type of function that can pause and resume execution.

```python
async def fetch_data():
    await asyncio.sleep(1)
    return "Data fetched"
```

### Event Loop
The event loop is the core of async programming. It runs asynchronous tasks and callbacks, handles I/O operations, and manages subprocesses.

```python
import asyncio

async def main():
    result = await fetch_data()
    print(result)

asyncio.run(main())
```

### Tasks
Tasks are used to schedule coroutines concurrently. When a coroutine is wrapped into a Task, it's automatically scheduled to run soon.

```python
async def main():
    task1 = asyncio.create_task(fetch_data())
    task2 = asyncio.create_task(fetch_data())

    result1 = await task1
    result2 = await task2
```

## Common Async Patterns

### Concurrent Execution
```python
async def main():
    results = await asyncio.gather(
        fetch_data(),
        fetch_data(),
        fetch_data()
    )
```

### Timeout
```python
async def main():
    try:
        result = await asyncio.wait_for(fetch_data(), timeout=5.0)
    except asyncio.TimeoutError:
        print("Operation timed out")
```

### Async Context Managers
```python
class AsyncResource:
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()
```

## When to Use Async

Async is beneficial for:
- I/O-bound operations (network requests, file I/O)
- Operations that spend time waiting
- Building responsive applications

Not ideal for:
- CPU-bound operations (use multiprocessing instead)
- Simple scripts with linear execution
