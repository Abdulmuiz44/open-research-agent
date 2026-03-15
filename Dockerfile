FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY apps /app/apps
COPY src /app/src

RUN pip install --no-cache-dir .

RUN useradd --create-home --shell /bin/bash ora
RUN mkdir -p /app/outputs && chown -R ora:ora /app
USER ora

EXPOSE 8000

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
