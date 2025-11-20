# Purple Agent Dockerfile - Home Automation Agent
FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port for Purple Agent
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/.well-known/agent-card.json || exit 1

# Run the Purple Agent
CMD ["python", "purple_agents/home_automation_agent.py", "--host", "0.0.0.0", "--port", "8000"]