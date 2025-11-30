# Docker Guide for Python Applications

## Introduction to Docker

Docker is a platform for developing, shipping, and running applications in containers. Containers allow you to package an application with all of its dependencies into a standardized unit for software development.

## Why Use Docker?

- **Consistency**: Same environment across development, testing, and production
- **Isolation**: Each application runs in its own container
- **Portability**: Containers can run on any system that supports Docker
- **Efficiency**: Containers share the host OS kernel, making them lightweight

## Getting Started with Python and Docker

### Creating a Dockerfile

A Dockerfile is a text file that contains instructions for building a Docker image. Here's a basic Dockerfile for a Python application:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

### Building the Image

To build your Docker image, run:

```bash
docker build -t myapp .
```

This command builds an image with the tag "myapp" using the Dockerfile in the current directory.

### Running the Container

Once the image is built, you can run it:

```bash
docker run -p 8000:8000 myapp
```

This maps port 8000 in the container to port 8000 on your host machine.

## Best Practices

1. **Use specific Python versions**: Instead of `python:latest`, use `python:3.11-slim`
2. **Minimize layers**: Combine RUN commands when possible
3. **Use .dockerignore**: Exclude unnecessary files from the build context
4. **Don't run as root**: Create a non-root user in your Dockerfile
5. **Multi-stage builds**: Use multi-stage builds to reduce final image size

## Docker Compose

For applications with multiple services, use Docker Compose:

```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
  redis:
    image: redis:alpine
```

Run with:

```bash
docker-compose up
```

## Conclusion

Docker simplifies deployment and ensures consistency across environments. Start with simple containers and gradually adopt more advanced features as needed.
