# FROM node:18-alpine
# WORKDIR /app

# # Install pnpm
# RUN npm install -g pnpm

# # # Copy package.json and pnpm-lock.yaml
# COPY package.json pnpm-lock.yaml ./

# # Install dependencies
# RUN pnpm install

# # Copy the rest of the application code
# COPY . .

# # # Build the application
# # RUN pnpm run build

# EXPOSE 4000

# CMD [ "pnpm", "start" ]

# # Use the official Node.js image as the base image
# FROM node:18-alpine AS build

# # Set the working directory
# WORKDIR /app

# # Copy package.json and pnpm-lock.yaml
# COPY package.json pnpm-lock.yaml ./

# # Install pnpm
# RUN npm install -g pnpm

# # Install dependencies
# RUN pnpm install

# # Copy the rest of the application code
# COPY . .

# # Build the application
# RUN pnpm run build

# # Use the official Nginx image to serve the application
# FROM nginx:alpine

# # Copy the build output to the Nginx HTML directory
# COPY --from=build /app/build /usr/share/nginx/html

# # Copy custom Nginx configuration file
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# # Expose port 8000
# EXPOSE 8000

# # Start Nginx server
# CMD ["nginx", "-g", "daemon off;"]

# Stage 1: Build the React application
FROM node:18-alpine AS build
WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy package.json and pnpm-lock.yaml
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install

# Copy the rest of the application code
COPY . .

# Build the application
RUN pnpm run build

# Stage 2: Serve the app with Nginx
FROM nginx:alpine
RUN apk add --no-cache gettext
WORKDIR /usr/share/nginx/html

# Remove default Nginx static files
RUN rm -rf ./*

# Copy build artifacts from the previous stage
COPY --from=build /app/build .

# Copy custom entrypoint script
COPY docker-entrypoint.sh /usr/bin/
RUN chmod +x /usr/bin/docker-entrypoint.sh

# Copy Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]