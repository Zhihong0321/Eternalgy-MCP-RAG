# Start with a Python 3.12 base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Copy initial MCP servers (these will be seeded to the volume on startup)
COPY mcp_servers /app/initial_mcp_servers

# Create a non-root user and switch to it
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application (use Railway/Heroku-style $PORT when provided)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
