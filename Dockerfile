FROM python:3.6.8-slim

RUN mkdir /app
WORKDIR /app

# Base install
RUN apt-get update && apt-get install -y zip git
RUN pip3 install --upgrade pip setuptools

# Add local files
COPY flask_pie flask_pie
COPY setup.py requirements.txt ./

# Install Pie and Pie Webapp requirements
RUN pip3 install $(cat requirements.txt) \
    https://download.pytorch.org/whl/cpu/torch-1.1.0-cp36-cp36m-linux_x86_64.whl \
    gunicorn && python3 setup.py install && python3 setup.py clean && rm -rf flask_pie && rm setup.py requirements.txt

