# Use the node image from official Docker Hub
FROM node:18.16.0-alpine3.16 AS build-stage

ENV NODE_OPTIONS="--openssl-legacy-provider"

ARG INCLUDE_EXAMPLES=false
ENV VUE_APP_INCLUDE_EXAMPLES=${INCLUDE_EXAMPLES}
ENV VUE_APP_DOCKER=true

# set the working directory
WORKDIR /app

# Copy the working directory in the container
COPY package*.json ./

# Install the project dependencies
RUN npm install

# Copy the rest of the project files to the container
COPY . .

# Build the Vue.js application to the production mode to dist folder
RUN npm run build

# Use the lightweight Nginx image from the previous stage for the nginx container
FROM nginx:stable-alpine AS production-stage

# Copy the build application from the previous stage to the Nginx container
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Expose the port 80
EXPOSE 80

# Start Nginx to serve the application
CMD ["nginx", "-g", "daemon off;"]