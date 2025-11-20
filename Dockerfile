# Green Agent Dockerfile - Cybersecurity Evaluator
FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create reports directory for output
RUN mkdir -p /app/reports

# Add src directory to Python path for local agentbeats module
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

# Expose port for Green Agent
EXPOSE 9010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9010/.well-known/agent-card.json || exit 1

# Run the Green Agent
CMD ["python", "green_agents/cybersecurity_evaluator.py", "--host", "0.0.0.0", "--port", "9010"]