FROM python:3.6.8

RUN mkdir /app
WORKDIR /app

# Base install
RUN apt-get update && apt-get install -y zip git
RUN pip3 install --upgrade pip setuptools

# Install Pie and Pie Webapp requirements
RUN pip3 install flask_pie https://download.pytorch.org/whl/cpu/torch-1.1.0-cp36-cp36m-linux_x86_64.whl gunicorn

