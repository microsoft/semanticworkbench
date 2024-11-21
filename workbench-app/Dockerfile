ARG VITE_SEMANTIC_WORKBENCH_SERVICE_URL

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