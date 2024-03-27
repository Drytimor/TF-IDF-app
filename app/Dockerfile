# syntax=docker/dockerfile:1

FROM python:3.12.1-alpine3.19

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app


# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=2000
ARG GID=2000
RUN addgroup -g "${GID}" appuser \
    && adduser -u "${UID}" -G appuser -s 'bin/sh' -g '' -D appuser

#RUN apk add postgresql-client postgresql-dev build-base


COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

#RUN --mount=type=cache,target=/root/.cache/pip \
#    --mount=type=bind,source=requirements.txt,target=requirements.txt \
#    python -m pip install -r requirements.txt

# Switch to the non-privileged user to run the application.
USER appuser

# Copy the source code into the container.
COPY --chown=appuser:appuser .. .

# Expose the port that the application listens on.

# Run the application.
CMD uvicorn main:app --reload --host 0.0.0.0 --port 8000