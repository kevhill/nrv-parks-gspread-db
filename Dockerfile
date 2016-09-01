# Taken from https://nodejs.org/en/docs/guides/nodejs-docker-webapp/
FROM node:argon

# Create app directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# some npm modules need to be installed globally
RUN npm install -g finalhandler postgraphql

# Bundle app source
COPY . /usr/src/app

EXPOSE 8080
CMD [ "postgraphql", "'$DATABASE_URL' --schema $DATABASE_SCHEMA --development"]