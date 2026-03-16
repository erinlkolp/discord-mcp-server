FROM python:3.12-slim

WORKDIR /app

# Copy project files
COPY requirements-lock.txt pyproject.toml ./
COPY src/ src/

# Install pinned dependencies, then the package itself
RUN pip install --no-cache-dir -r requirements-lock.txt && pip install --no-cache-dir --no-deps .

# Run as non-root user
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Run the MCP server
ENTRYPOINT ["discord-mcp"]
