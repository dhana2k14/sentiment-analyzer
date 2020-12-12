FROM ubuntu:18.04

RUN apt-get -y update 
RUN apt-get -y install ca-certificates python3-pip && pip3 install --upgrade pip

WORKDIR /app
COPY . /app

RUN pip3 --no-cache-dir install -r requirements.txt

EXPOSE 5006

ENTRYPOINT [ "python3" ]
CMD [ "app.py"]
