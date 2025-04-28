FROM nginx:alpine

# Copy nginx config
COPY ./nginx/default.conf /etc/nginx/conf.d/default.conf

# Copy all frontend static files
COPY . /usr/share/nginx/html

EXPOSE 80
