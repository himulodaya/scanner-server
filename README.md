# Scanner Server

A modern, self-hosted document scanning and printing server with OCR capabilities, Discord integration, and a clean web interface.

## Features

- **Document Scanning**: Single-page and multi-page scanning from network scanners (HP devices with eSCL/AirPrint support)
- **OCR Processing**: Automatic optical character recognition using Tesseract to create searchable PDFs
- **Print Management**: Web-based file uploading and printing to network printers
- **Document Organization**: Automatic categorization (invoices, receipts, letters, miscellaneous)
- **Discord Notifications**: Real-time notifications via webhook when scans complete
- **NFC Support**: Tap-to-scan capability via NFC tags
- **Modern Architecture**: Multi-stage Docker builds, production-ready with Gunicorn
- **Security**: Rate limiting, input validation, secure file handling
- **Health Checks**: Built-in health monitoring for Docker deployments

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Network-accessible HP scanner (with eSCL/AirPrint support)
- Network-accessible printer (optional, for printing features)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/scanner-server.git
   cd scanner-server
   ```

2. Create environment configuration:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` file with your scanner IP and settings:
   ```bash
   SCANNER_IP=192.168.1.100
   SCANNER_PROTOCOL=escl
   SCANNER_PORT=443
   ```

4. Start the server:
   ```bash
   docker-compose up -d
   ```

5. Access the web interface at `http://localhost:5000`

## Configuration

### Environment Variables

See `.env.example` for all available configuration options:

| Variable | Description | Default |
|----------|-------------|---------|
| `SCANNER_IP` | IP address of your network scanner | `192.168.1.100` |
| `SCANNER_PROTOCOL` | Protocol to use (escl or hpaio) | `escl` |
| `SCANNER_PORT` | Scanner port | `443` |
| `FLASK_DEBUG` | Enable debug mode (0 or 1) | `0` |
| `GUNICORN_WORKERS` | Number of Gunicorn workers | `2` |
| `LOG_LEVEL` | Logging level | `info` |
| `OCR_LANGUAGE` | Tesseract language pack | `eng` |
| `DISCORD_WEBHOOK_URL` | Discord webhook for notifications | (empty) |

### Scanner Configuration

The server supports HP scanners with eSCL (AirPrint/AirScan) protocol. To configure:

1. Find your scanner's IP address (check your router or scanner settings)
2. Set `SCANNER_IP` in your `.env` file
3. For older HP scanners, you may need to use `hpaio` protocol instead of `escl`

### Discord Integration

To enable Discord notifications:

1. Create a Discord webhook in your server settings
2. Set `DISCORD_WEBHOOK_URL` in your `.env` file
3. Test the webhook in the Settings page

## Architecture

### Technology Stack

- **Backend**: Flask 3.1.0 with Gunicorn
- **Frontend**: Modern HTML/CSS/JavaScript
- **OCR**: Tesseract OCR with OCRmyPDF
- **Image Processing**: Pillow, ImageMagick
- **Printing**: CUPS (Common Unix Printing System)
- **Scanning**: SANE with HPLIP drivers
- **Container**: Ubuntu 24.04 LTS with multi-stage build

### Project Structure

```
scanner-server/
├── backend/
│   ├── __init__.py
│   ├── app.py              # Flask application
│   ├── config.py           # Configuration management
│   ├── api/
│   │   ├── scanner.py      # Scanning operations
│   │   ├── printer.py      # Printing operations
│   │   └── settings.py     # Settings management
│   └── utils/
│       ├── ocr.py          # OCR processing
│       ├── pdf.py          # PDF manipulation
│       └── notifications.py # Discord integration
├── frontend/
│   ├── templates/          # Jinja2 templates
│   └── static/
│       ├── css/           # Stylesheets
│       └── js/            # JavaScript
├── config/
│   └── default_config.json # Default configuration
├── tests/                  # Unit tests
├── Dockerfile             # Multi-stage build
├── docker-compose.yml     # Docker Compose configuration
└── requirements.txt       # Python dependencies
```

## API Endpoints

### Scanning

- `GET /api/scan/single` - Scan a single page
- `GET /api/scan/start_multi` - Start multi-page session
- `GET /api/scan/page/<session_id>` - Scan additional page
- `GET /api/scan/finish/<session_id>` - Finalize multi-page scan

### Printing

- `GET /api/printer/list` - List available printers
- `POST /api/printer/print` - Upload and print a file

### Settings

- `GET /api/settings` - Get current settings
- `POST /api/settings/update` - Update settings
- `POST /api/settings/test_scanner` - Test scanner connection
- `POST /api/settings/test_discord` - Test Discord webhook

### System

- `GET /health` - Health check endpoint

## NFC Support

Create quick-scan shortcuts using NFC tags:

1. Write URL to NFC tag: `http://your-server-ip:5000/nfc/single_scan`
2. Tap your NFC-enabled phone on the tag
3. The scan will start automatically

For multi-page scans: `http://your-server-ip:5000/nfc/multi_scan`

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with coverage
pytest --cov=backend
```

### Local Development

```bash
# Set debug mode
export FLASK_DEBUG=1

# Run without Docker
python -m backend.app
```

## Security Considerations

- The container requires privileged mode for SANE scanner access
- Rate limiting is enabled (200 requests/day, 50/hour per IP)
- File uploads are limited to 50MB
- Input validation and sanitization on all endpoints
- Security headers and CSRF protection recommended for production

## Deployment

### Production Recommendations

1. Use environment variables for sensitive configuration
2. Set up reverse proxy (nginx/Traefik) with HTTPS
3. Configure proper firewall rules
4. Use Docker secrets for sensitive data
5. Enable automatic backups of scan data volume
6. Monitor with health check endpoint
7. Review and adjust resource limits

### Docker Compose Production Example

```yaml
services:
  scanner-server:
    build: .
    restart: always
    environment:
      - FLASK_DEBUG=0
      - GUNICORN_WORKERS=4
      - LOG_LEVEL=warning
    volumes:
      - ./config:/config:ro
      - scanner_data:/data/scan
    networks:
      - web
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.scanner.rule=Host(`scanner.example.com`)"
```

## Troubleshooting

### Scanner Not Found

1. Verify scanner IP address is correct
2. Ensure scanner supports eSCL/AirPrint protocol
3. Check network connectivity: `ping <scanner-ip>`
4. Try switching between `escl` and `hpaio` protocols

### OCR Not Working

1. Check Tesseract language pack is installed
2. Verify OCR is enabled in settings
3. Check container logs: `docker-compose logs scanner-server`

### Printing Issues

1. Verify CUPS is running: `docker exec scanner-server lpstat -r`
2. List printers: `docker exec scanner-server lpstat -p -d`
3. Check printer connection and drivers

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Changelog

### Version 2.0.0 (2025-01-08)

- Modernized Docker build with multi-stage architecture
- Upgraded to Ubuntu 24.04 LTS
- Updated all Python dependencies to latest versions
- Added production-ready Gunicorn configuration
- Implemented comprehensive error handling and logging
- Added rate limiting and security improvements
- Created modern CSS/JavaScript frontend
- Added health check endpoints
- Implemented unit test structure
- Enhanced documentation and deployment guides
- Added environment-based configuration with .env support
- Improved Docker Compose with resource limits and labels

## Support

For issues, questions, or contributions, please visit:
- GitHub Issues: https://github.com/yourusername/scanner-server/issues
- Documentation: https://github.com/yourusername/scanner-server/wiki

---

Made with care for the open-source community
