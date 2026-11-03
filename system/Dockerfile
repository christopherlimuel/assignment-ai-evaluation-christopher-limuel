FROM python:3.11-slim

WORKDIR /app

# Copy dependencies first so installing them can be cached independently of source changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application and its data files.
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
