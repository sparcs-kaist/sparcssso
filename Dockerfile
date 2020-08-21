FROM python:3.6-alpine

# Create user, Set workdir
RUN addgroup -g 1000 sparcssso \
 && adduser -S -u 1000 -G sparcssso sparcssso

WORKDIR /usr/app/sparcssso

# Install packages, which is needed for SPARCS SSO
# Install build dependencies as virtual package so they can be reverted easily
RUN apk add --no-cache git mariadb-connector-c-dev jpeg-dev zlib-dev \
 && apk add --no-cache --virtual .build-deps build-base mariadb-dev linux-headers

# Install uWSGI
RUN pip install --no-cache-dir uwsgi

# Install requirements first, so we don't need to build again from installing
COPY --chown=sparcssso:sparcssso requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Revert build dependencies
RUN apk del .build-deps

# Copy SPARCS SSO application
COPY --chown=sparcssso:sparcssso . .

# Set user
USER sparcssso:sparcssso

# Run on 9090
EXPOSE 9090
CMD ["uwsgi", "--socket", "0.0.0.0:9090", "--module", "sparcssso.wsgi"]
