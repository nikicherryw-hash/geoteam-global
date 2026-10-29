FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY sourcing/search_v2/requirements.txt /tmp/geoteam-requirements.txt
RUN pip install --no-cache-dir -r /tmp/geoteam-requirements.txt \
    && groupadd -g 10001 geoteam && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin geoteam
COPY sourcing/search_v2 /app/sourcing/search_v2
COPY sourcing/backend/functions/source_registry.json /app/sourcing/backend/functions/source_registry.json
RUN mkdir -p /data && chown -R 10001:10001 /data /app
USER 10001:10001
EXPOSE 8080
CMD ["uvicorn","sourcing.search_v2.agent_service:app","--host","0.0.0.0","--port","8080","--workers","1","--no-access-log"]
