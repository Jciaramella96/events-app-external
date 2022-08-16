# use base image for NODEJS
FROM node:14-alpine
# copy app code
COPY . /app/

#change the working directory
WORKDIR /app

#install dependecies

RUN npm install

# start the express app
CMD ["node", "server.js"]


