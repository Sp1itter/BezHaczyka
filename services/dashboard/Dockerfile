# Panel: build Vite serwowany przez nginx (nie-root, 8080 w kontenerze).
FROM node:20.18.1-bookworm-slim AS build
WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.27.3-alpine
# Szablon: obraz podstawia ${API_UPSTREAM} przy starcie (envsubst).
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /src/dist /usr/share/nginx/html
ENV API_UPSTREAM=http://dashboard-mock:4000
EXPOSE 8080
