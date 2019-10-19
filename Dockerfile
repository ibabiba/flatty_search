FROM python:3.6-stretch
RUN apt-get update -y && pip install --upgrade pip
WORKDIR /app
COPY requirements.txt /app
RUN pip install -r ./requirements.txt
COPY . .
CMD ["python", "engine.py"]
