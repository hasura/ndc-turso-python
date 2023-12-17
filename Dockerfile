# Use the official Python image from the Docker Hub
FROM python:3.10-slim-buster

# Set the working directory
WORKDIR /usr/src/app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY ./main.py .

CMD ["python", "main.py", "serve", "--configuration", "config.json", "--port", "8084"]