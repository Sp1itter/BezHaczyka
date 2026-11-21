# Obraz dashboardu (osoba C): statyczny build Vite serwowany przez nginx.
# Build z services/web: docker build -t investwatch-web .

FROM node:20.18.1-bookworm-slim AS build
WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY index.html vite.config.js ./
COPY src/ ./src/
RUN npm run build

# nginx-unprivileged: dziala jako nie-root (wymog bezpieczenstwa), slucha na 8080.
FROM nginxinc/nginx-unprivileged:1.27.3-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/dist /usr/share/nginx/html
EXPOSE 8080
