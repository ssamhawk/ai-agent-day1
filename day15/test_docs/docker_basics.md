# Docker Basics

## What is Docker?

Docker is a platform for developing, shipping, and running applications in containers. Containers are lightweight, portable, and isolated environments that package an application with all its dependencies.

## Key Docker Concepts

### Containers
A container is a runnable instance of an image. You can create, start, stop, move, or delete a container using the Docker API or CLI.

### Images
A Docker image is a read-only template with instructions for creating a Docker container. Images are built from a Dockerfile.

### Dockerfile
A Dockerfile is a text document that contains commands to assemble an image. Common commands include:
- FROM: Specifies the base image
- RUN: Executes commands in the container
- COPY: Copies files from host to container
- CMD: Specifies the default command to run

## Basic Docker Commands

```bash
# Pull an image
docker pull nginx

# Run a container
docker run -d -p 80:80 nginx

# List running containers
docker ps

# Stop a container
docker stop container_id

# Remove a container
docker rm container_id
```

## Docker Compose

Docker Compose is a tool for defining and running multi-container Docker applications. You use a YAML file to configure your application's services.

Example docker-compose.yml:
```yaml
version: '3'
services:
  web:
    image: nginx
    ports:
      - "80:80"
  db:
    image: postgres
    environment:
      POSTGRES_PASSWORD: example
```
