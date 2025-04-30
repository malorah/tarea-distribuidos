FROM python:3.13-slim

WORKDIR /app

COPY ./Scrapper/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt 

COPY ./Scrapper /app  


CMD ["python", "Main.py"] 
