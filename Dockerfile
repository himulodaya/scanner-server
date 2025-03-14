FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install necessary packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    sane-utils \
    imagemagick \
    tesseract-ocr \
    cups \
    cups-client \
    hplip \
    hplip-gui \
    printer-driver-hpcups \
    ocrmypdf \
    pdftk \
    libsane-hpaio \
    wget \
    curl \
    nano \
    libpng-dev \
    libjpeg-dev \
    libtiff-dev \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick policy to allow PDF conversion
RUN sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml

# Configure CUPS to allow remote access
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

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /data/scan/temp /data/scan/invoices /data/scan/receipts /data/scan/letters /data/scan/misc
RUN chmod -R 755 /data/scan

# Create a startup script
RUN echo '#!/bin/bash' > /start.sh && \
    echo 'service cups start' >> /start.sh && \
    echo 'python3 -m backend.app' >> /start.sh && \
    chmod +x /start.sh

# Expose ports for web interface and CUPS
EXPOSE 5000 631

# Set entrypoint
ENTRYPOINT ["/start.sh"]
