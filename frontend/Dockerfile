# Production Nginx Container
FROM nginx:alpine

# Copy pre-built production bundle and Nginx configuration
COPY dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
