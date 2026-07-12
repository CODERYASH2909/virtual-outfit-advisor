# Multi-stage build: compile Tailwind CSS + TypeScript, then serve with Nginx
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/index.html /usr/share/nginx/html/index.html
COPY --from=build /app/pages /usr/share/nginx/html/pages
COPY --from=build /app/public /usr/share/nginx/html/public
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
