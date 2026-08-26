FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm config set registry https://registry.npmjs.org/ \
    && npm config set cache /root/.npm \
    && npm ci --prefer-offline --no-audit --progress=false

COPY . .

ARG VITE_API_BASE_URL=/api/v1
ARG VITE_NESHAN_SERVICE_KEY=
ARG VITE_NESHAN_REVERSE_URL=https://api.neshan.org/v5/reverse

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_NESHAN_SERVICE_KEY=${VITE_NESHAN_SERVICE_KEY}
ENV VITE_NESHAN_REVERSE_URL=${VITE_NESHAN_REVERSE_URL}

RUN npm run build

FROM nginx:1.27-alpine

COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
