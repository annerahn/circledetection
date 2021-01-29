# start with a base image
FROM ubuntu:18.04

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Moscow

RUN apt-get update -y && apt-get install -y build-essential cmake \
libsm6 libxext6 libxrender-dev \
python3 python3-pip python3-dev

RUN pip3 install --upgrade pip

RUN pip3 -V

COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install -r requirements.txt

COPY . /app
ENTRYPOINT ["python3"]
CMD ["circledetection.py"]