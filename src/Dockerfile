# ==========================================
# STAGE 1: Base Setup (The "Builder")
# ==========================================
# We use 'slim' to keep the image size small, reducing the attack surface.
FROM python:3.11-slim AS builder

# Prevent Python from writing .pyc files and force stdout logging (no buffering)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a specific directory for our app
WORKDIR /app

# Copy only the necessary code into the image
COPY server.py .

# ==========================================
# STAGE 2: Production Execution
# ==========================================
FROM python:3.11-slim AS runner

ENV PYTHONUNBUFFERED=1

# Security Best Practice: Never run containers as root
RUN useradd -m proxyuser

WORKDIR /app

# Copy the script from the builder stage
COPY --from=builder /app/server.py /app/server.py

RUN chown -R proxyuser:proxyuser /app

# Switch to the non-root user
USER proxyuser

# Expose the port so Docker knows this container listens here
EXPOSE 56000

# The command to run when the container starts
CMD ["python", "server.py"]