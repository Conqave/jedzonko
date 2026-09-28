FROM node:22-alpine AS dependencies
WORKDIR /workspace
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts


FROM dependencies AS tools
ENV PATH=/workspace/node_modules/.bin:$PATH
WORKDIR /workspace/frontend


FROM dependencies AS build
WORKDIR /workspace/frontend
COPY . .
ENV PATH=/workspace/node_modules/.bin:$PATH
RUN quasar prepare --silent && quasar build


FROM nginx:1.29-alpine AS runtime
COPY --from=build /workspace/frontend/dist/spa /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
