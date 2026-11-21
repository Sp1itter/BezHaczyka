FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
COPY casedb ./casedb
RUN pip install --no-cache-dir . && rm -rf /app/casedb /app/pyproject.toml
RUN useradd --system --uid 10001 casedb
USER casedb

ENTRYPOINT ["python", "-m", "casedb"]
CMD ["init"]
