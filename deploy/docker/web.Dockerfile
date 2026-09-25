# Optional: build the Flutter Web app inside Docker (CI / machines without Flutter installed).
# The local docker-compose stack instead mounts frontend/build/web built on the laptop.
#
#   docker build -f deploy/docker/web.Dockerfile -t dms-web:local \
#     --build-arg FLUTTER_IMAGE=<artifactory>/cirruslabs/flutter:stable \
#     --build-arg PUB_HOSTED_URL=https://<artifactory>/artifactory/api/pub/<pub-repo> \
#     --build-arg FLUTTER_STORAGE_BASE_URL=https://<artifactory>/artifactory/<flutter-storage-repo> .
ARG FLUTTER_IMAGE=ghcr.io/cirruslabs/flutter:stable
ARG NGINX_IMAGE=nginxinc/nginx-unprivileged:stable-alpine

FROM ${FLUTTER_IMAGE} AS build
ARG PUB_HOSTED_URL=""
ARG FLUTTER_STORAGE_BASE_URL=""
WORKDIR /src
COPY frontend/pubspec.yaml ./
RUN set -eu; \
    [ -n "$PUB_HOSTED_URL" ] && export PUB_HOSTED_URL || unset PUB_HOSTED_URL; \
    [ -n "$FLUTTER_STORAGE_BASE_URL" ] && export FLUTTER_STORAGE_BASE_URL || unset FLUTTER_STORAGE_BASE_URL; \
    flutter pub get
COPY frontend/ ./
RUN set -eu; \
    [ -n "$PUB_HOSTED_URL" ] && export PUB_HOSTED_URL || unset PUB_HOSTED_URL; \
    [ -n "$FLUTTER_STORAGE_BASE_URL" ] && export FLUTTER_STORAGE_BASE_URL || unset FLUTTER_STORAGE_BASE_URL; \
    flutter build web --release --no-web-resources-cdn

FROM ${NGINX_IMAGE}
COPY deploy/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY deploy/nginx/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=build /src/build/web /usr/share/nginx/html
EXPOSE 8080
