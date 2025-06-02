#!/bin/bash

source distri/bin/activate
sudo docker-compose up -d cache mongodb storage-api
sudo docker-compose up -d --build scraper
sudo docker-compose up -d --build traffic-generator
python3 stats.py
