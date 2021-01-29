# start with a base image
FROM python:3-slim
EXPOSE 8080

COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install -r requirements.txt

COPY . /app
ENTRYPOINT ["python3"]
CMD ["circledetection.py"]