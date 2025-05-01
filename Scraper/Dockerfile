FROM python:3

ENV MONGO_DB_USERNAME=admin
ENV MONGO_DB_PWD=password

RUN mkdir -p /home/scrapper

RUN python -m pip install pymongo
RUN pip3 install pymongo
RUN pip3 install requests

COPY . /home/scrapper


CMD ["python","./home/scrapper/scrapper.py"]





