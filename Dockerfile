FROM python:3.10-slim-buster

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY entrypoint.sh .

RUN chmod +x entrypoint.sh

EXPOSE 8084


ENTRYPOINT ["./entrypoint.sh"]
