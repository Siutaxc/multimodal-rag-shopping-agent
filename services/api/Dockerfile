FROM python:3.13-slim@sha256:6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN addgroup --system --gid 1001 shoplens && adduser --system --uid 1001 --ingroup shoplens shoplens
COPY services/api/pyproject.toml ./pyproject.toml
COPY services/api/app ./app
COPY services/api/alembic.ini ./alembic.ini
COPY services/api/migrations ./migrations
COPY data/fixtures ./data/fixtures
RUN python -m pip install --no-cache-dir --retries 10 --timeout 120 .
RUN mkdir -p /app/data/storage && chown -R shoplens:shoplens /app/data/storage

USER shoplens
EXPOSE 8000
CMD ["sh", "-c", "python -m alembic -c alembic.ini upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
