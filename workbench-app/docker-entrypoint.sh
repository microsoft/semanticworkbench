#!/bin/sh

# Replace placeholders in static files with environment variables
envsubst '$VITE_SEMANTIC_WORKBENCH_SERVICE_URL' < /usr/share/nginx/html/index.html > /usr/share/nginx/html/index.html.tmp
mv /usr/share/nginx/html/index.html.tmp /usr/share/nginx/html/index.html

envsubst '$PORT' < /etc/nginx/conf.d/default.conf > /etc/nginx/conf.d/default.conf.tmp
mv /etc/nginx/conf.d/default.conf.tmp /etc/nginx/conf.d/default.conf

echo "VITE_SEMANTIC_WORKBENCH_SERVICE_URL = $VITE_SEMANTIC_WORKBENCH_SERVICE_URL"
echo "PORT = $PORT"

exec "$@"