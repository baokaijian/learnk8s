FROM docker.io/python:3.13-alpine
WORKDIR /site
COPY --chown=1000:1000 index.html /site/index.html
ENV PYTHONUNBUFFERED=1
USER 1000:1000
EXPOSE 8080
CMD ["python3", "-m", "http.server", "8080", "--bind", "0.0.0.0", "--directory", "/site"]
