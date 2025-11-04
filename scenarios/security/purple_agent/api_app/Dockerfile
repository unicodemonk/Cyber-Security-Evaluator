
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build deps (kept minimal). Some wheels may need a compiler.
RUN apt-get update \
	&& apt-get install -y --no-install-recommends gcc build-essential \
	&& rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . /app

# Port used by Uvicorn
EXPOSE 8000

# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

