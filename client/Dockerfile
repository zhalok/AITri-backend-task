# ---- Stage 1: build the React app ---------------------------------------------------------------
FROM node:22-slim AS build
WORKDIR /client
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ---- Stage 2: nginx serves the build, terminates TLS, and forwards the API to the backend ----------
FROM nginx:1.27-alpine
RUN apk add --no-cache openssl
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY nginx/40-self-signed-cert.sh /docker-entrypoint.d/40-self-signed-cert.sh
RUN chmod +x /docker-entrypoint.d/40-self-signed-cert.sh
COPY --from=build /client/dist /usr/share/nginx/html
EXPOSE 80 443
