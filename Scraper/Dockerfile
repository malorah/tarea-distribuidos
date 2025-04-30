FROM python:3

ENV MONGO_DB_USERNAME=admin
ENV MONGO_DB_PWD=password

RUN mkdir -p /home/project

RUN python -m pip install pymongo
RUN pip3 install pymongo
RUN pip3 install requests

COPY . /home/project


CMD ["python","/home/project/scrapper.py"]





