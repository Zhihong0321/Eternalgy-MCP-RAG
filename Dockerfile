# Start with a Python 3.12 base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the backend requirements file and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code
COPY backend/ .

# Copy initial MCP servers (these will be seeded to the volume on startup)
# Note: backend/mcp_servers was copied into . via the line above, so it is at /app/mcp_servers
# We need to move it to /app/initial_mcp_servers to match the logic or adjust logic.
# The original Dockerfile copied mcp_servers to /app/initial_mcp_servers.
# Since 'COPY backend/ .' puts everything in /app/, 'mcp_servers' is now at '/app/mcp_servers'.
# We can just rename it or copy it again.
RUN cp -r mcp_servers /app/initial_mcp_servers

# Create a non-root user and switch to it
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
