# Taken from https://nodejs.org/en/docs/guides/nodejs-docker-webapp/
FROM node:argon

RUN apt-get update && apt-get install -y \
    python-dev \
	python-psycopg2 \
    build-essential \
    curl

# get latest version of pip
RUN curl -O https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py

# mounting just requirements.txt first will make our build caches a bit saner
ADD ./requirements.txt /requirements.txt

# Create app directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# some npm modules need to be installed globally
RUN npm install -g finalhandler postgraphql

# install other python required libs through pip
RUN pip install -r /requirements.txt

# Bundle app source
COPY . /usr/src/app

EXPOSE 8080
CMD [ "postgraphql", "'$DATABASE_URL' --schema $DATABASE_SCHEMA --development"]