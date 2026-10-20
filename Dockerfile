FROM node:22-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 ca-certificates && apt-get clean && npm install --global @qloo/qloo-harness@0.1.26
WORKDIR /app
COPY engine.py qloo.py fixtures.py experiment.py service.py server.py ./
COPY dist ./dist
USER node
ENV PORT=8080
EXPOSE 8080
CMD ["python3", "server.py", "--host", "0.0.0.0"]
