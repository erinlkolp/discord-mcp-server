FROM python:3.12-slim@sha256:ccc7089399c8bb65dd1fb3ed6d55efa538a3f5e7fca3f5988ac3b5b87e593bf0

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
