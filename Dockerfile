# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install the required dependencies (uvicorn + your app dependencies)
RUN pip install --no-cache-dir uv

# Copy the current directory contents into the container at /app
COPY . /app

# Expose the application port
EXPOSE 8000

# Command to run your FastAPI application with uvicorn
CMD ["uv", "run", "fastapi", "run", "main.py", "--port", "8082", "--reload"]
