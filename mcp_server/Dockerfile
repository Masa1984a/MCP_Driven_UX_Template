# Multi-stage build for Cloud MCP Server
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir --user -r requirements-cloud.txt

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable:
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY shared/ ./shared/
COPY auth/ ./auth/
COPY transport/ ./transport/
COPY cloud_mcp_server.py .

# Note: Running as root for debugging (should use non-root in production)
# RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser
# RUN chown -R mcpuser:mcpuser /app
# USER mcpuser

# Environment variables for Cloud Run
ENV MCP_CLOUD_MODE=true
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8080
ENV MCP_LOG_LEVEL=INFO
ENV MCP_AUTH_PROVIDER=api_key
ENV MCP_TRANSPORT_TYPE=streamable_http

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Start command
CMD ["python", "cloud_mcp_server.py"]