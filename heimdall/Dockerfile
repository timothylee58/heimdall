FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api api
COPY policies policies
COPY data data
RUN useradd --create-home heimdall && mkdir /state && chown heimdall /state
USER heimdall
ENV HEIMDALL_DB=/state/heimdall.sqlite3
EXPOSE 8000
CMD ["uvicorn", "api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
