FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN sed -i 's|pid\s*/run/nginx.pid;|pid /tmp/nginx.pid;|g' /etc/nginx/nginx.conf \
    && mkdir -p /tmp/nginx_client_body \
    && echo 'client_body_temp_path /tmp/nginx_client_body;' >> /etc/nginx/conf.d/default.conf \
    && chown -R appuser:appgroup /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d /tmp/nginx_client_body
USER appuser
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s CMD wget -qO- http://localhost/ || exit 1
