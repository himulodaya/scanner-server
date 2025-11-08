# Multi-stage build for Scanner Server
# Stage 1: Build dependencies
FROM ubuntu:24.04 AS builder

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM ubuntu:24.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    FLASK_APP=backend.app \
    CONFIG_DIR=/config \
    DATA_DIR=/data/scan

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    # Scanner support
    sane-utils \
    libsane-hpaio \
    hplip \
    # OCR support
    tesseract-ocr \
    tesseract-ocr-eng \
    ocrmypdf \
    # PDF processing
    pdftk \
    # Image processing
    imagemagick \
    # Printing support
    cups \
    cups-client \
    printer-driver-hpcups \
    # System utilities
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for application
# Note: CUPS and SANE typically need specific permissions
RUN groupadd -r scanner && \
    useradd -r -g scanner -G lpadmin scanner && \
    usermod -a -G scanner lp

# Set work directory
WORKDIR /app

# Copy application code
COPY --chown=scanner:scanner backend/ ./backend/
COPY --chown=scanner:scanner frontend/ ./frontend/
COPY --chown=scanner:scanner config/ ./config/

# Fix ImageMagick policy for PDF conversion
RUN sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml || \
    sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' /etc/ImageMagick-7/policy.xml || true

# Configure CUPS for network access
RUN echo 'ServerAlias *' >> /etc/cups/cupsd.conf && \
    echo 'Port 631' >> /etc/cups/cupsd.conf && \
    echo 'Listen /run/cups/cups.sock' >> /etc/cups/cupsd.conf && \
    echo 'Browsing On' >> /etc/cups/cupsd.conf && \
    echo 'BrowseLocalProtocols dnssd' >> /etc/cups/cupsd.conf && \
    echo 'DefaultAuthType Basic' >> /etc/cups/cupsd.conf && \
    echo 'WebInterface Yes' >> /etc/cups/cupsd.conf && \
    echo '<Location />' >> /etc/cups/cupsd.conf && \
    echo '  Order allow,deny' >> /etc/cups/cupsd.conf && \
    echo '  Allow all' >> /etc/cups/cupsd.conf && \
    echo '</Location>' >> /etc/cups/cupsd.conf && \
    echo '<Location /admin>' >> /etc/cups/cupsd.conf && \
    echo '  Order allow,deny' >> /etc/cups/cupsd.conf && \
    echo '  Allow all' >> /etc/cups/cupsd.conf && \
    echo '</Location>' >> /etc/cups/cupsd.conf && \
    echo '<Location /admin/conf>' >> /etc/cups/cupsd.conf && \
    echo '  AuthType Default' >> /etc/cups/cupsd.conf && \
    echo '  Require user @SYSTEM' >> /etc/cups/cupsd.conf && \
    echo '  Order allow,deny' >> /etc/cups/cupsd.conf && \
    echo '  Allow all' >> /etc/cups/cupsd.conf && \
    echo '</Location>' >> /etc/cups/cupsd.conf

# Create directories with proper permissions
RUN mkdir -p /data/scan/temp \
    /data/scan/invoices \
    /data/scan/receipts \
    /data/scan/letters \
    /data/scan/misc \
    /config && \
    chown -R scanner:scanner /data /config

# Create improved startup script
COPY <<'EOF' /start.sh
#!/bin/bash
set -e

# Start CUPS service
echo "Starting CUPS service..."
service cups start

# Wait for CUPS to be ready
timeout=10
while [ $timeout -gt 0 ] && ! lpstat -r &>/dev/null; do
    echo "Waiting for CUPS to be ready..."
    sleep 1
    ((timeout--))
done

if lpstat -r &>/dev/null; then
    echo "CUPS is ready"
else
    echo "Warning: CUPS may not be fully ready"
fi

# Start the Flask application with Gunicorn
echo "Starting Scanner Server..."
cd /app

# Check if we should use debug mode (default: production)
if [ "${FLASK_DEBUG}" = "1" ]; then
    echo "Running in DEBUG mode"
    exec python3 -m flask run --host=0.0.0.0 --port=5000
else
    echo "Running in PRODUCTION mode with Gunicorn"
    exec gunicorn \
        --bind 0.0.0.0:5000 \
        --workers ${GUNICORN_WORKERS:-2} \
        --timeout ${GUNICORN_TIMEOUT:-120} \
        --access-logfile - \
        --error-logfile - \
        --log-level ${LOG_LEVEL:-info} \
        'backend.app:app'
fi
EOF

RUN chmod +x /start.sh

# Expose ports
# 5000: Web interface
# 631: CUPS web interface
EXPOSE 5000 631

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Note: This container needs to run in privileged mode for SANE scanner access
# See docker-compose.yml for the privileged: true setting

# Run as root for CUPS/SANE access (required for scanner/printer operations)
# In production, you might want to use capabilities instead:
# --cap-add=DAC_READ_SEARCH --cap-add=NET_RAW --device /dev/bus/usb

ENTRYPOINT ["/start.sh"]
