FROM python:3.12-slim

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install the package (hatchling build backend is pulled in automatically)
RUN pip install --no-cache-dir .

# Run the MCP server
ENTRYPOINT ["discord-mcp"]
