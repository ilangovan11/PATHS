FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Start nginx directly. We do NOT use the image's docker-entrypoint.sh because
# its 10-listen-on-ipv6-by-default.sh helper hangs in some container runtimes
# (observed: 'apk manifest nginx' blocks, so nginx never launches).
ENTRYPOINT ["nginx", "-g", "daemon off;"]