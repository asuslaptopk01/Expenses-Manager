FROM python:3.12-alpine

WORKDIR /app

# Install system dependencies if required
RUN apk add --no-cache gcc musl-dev postgresql-dev

COPY req.txt .
RUN pip install --no-cache-dir -r req.txt

# This copies everything from your local project into the container's /app directory
COPY . /app/

EXPOSE 8001