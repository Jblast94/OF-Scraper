# OF-Scraper Deployment Guide

This comprehensive guide covers the deployment and usage of the OF-Scraper application, including containerized setup, UI integration, and troubleshooting.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Container Deployment](#container-deployment)
3. [Environment Configuration](#environment-configuration)
4. [UI Usage](#ui-usage)
5. [Common Workflows](#common-workflows)
6. [Troubleshooting](#troubleshooting)
7. [Health Checks & Monitoring](#health-checks--monitoring)

## Prerequisites

Before proceeding with deployment, ensure you have:

- **Docker Engine** 20.10 or later
- **Docker Compose** 2.0 or later
- **Python 3.10+** (for local development)
- **Git** (for cloning the repository)
- **At least 2GB RAM** and **2GB disk space**

## Container Deployment

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd OF-Scraper

# Copy environment template
cp .env.example .env
```

### 2. Environment Configuration

Create and configure your `.env` file:

```bash
# Required: Your API key for authentication
OF_API_KEY=your_api_key_here

# Optional: Download directory (defaults to /app/data)
OF_DOWNLOAD_PATH=/app/data

# Optional: Build version override
BUILD_VERSION=1.0.0
```

### 3. Build and Run with Docker Compose

```bash
# Build the container image
docker-compose build

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Manual Docker Commands

For more control, use Docker directly:

```bash
# Build image
docker build -t of-scraper:latest .

# Run container
docker run -d \
  --name ofscraper \
  -e OF_API_KEY=your_api_key \
  -e OF_DOWNLOAD_PATH=/app/data \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config:/home/ofscraper/.config/ofscraper \
  of-scraper:latest
```

### 5. Docker Compose Configuration Options

The `docker-compose.yml` provides several configuration patterns:

#### Interactive Mode (Recommended)
```yaml
services:
  of-scraper:
    stdin_open: true
    tty: true
    command: ["/bin/bash", "-c", "sleep infinity"]
```

Usage:
```bash
# Start container
docker-compose up -d

# Run commands interactively
docker-compose exec -it ofscraper ofscraper --username ALL --posts all
```

#### Automated Mode
```yaml
services:
  of-scraper:
    command: "ofscraper --username ALL --posts all"
```

#### Development Mode
```yaml
services:
  of-scraper:
    volumes:
      - ./:/app
      - ./data:/app/data
    environment:
      - DEBUG=true
```

## Environment Configuration

### Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OF_API_KEY` | API authentication key | - | Yes |
| `OF_DOWNLOAD_PATH` | Download directory | `/app/data` | No |
| `USER_ID` | Host user ID for permissions | `1000` | No |
| `GROUP_ID` | Host group ID for permissions | `1000` | No |

### Volume Mounts

```yaml
volumes:
  # Configuration directory
  - ./config/:/home/ofscraper/.config/ofscraper/
  
  # Data storage directory  
  - ./data/:/app/data/
  
  # Optional: External binaries
  - /usr/bin/ffmpeg:/usr/bin/ffmpeg
```

## UI Usage

### Desktop UI (PySide6)

Launch the desktop application:

```bash
# Local installation
pip install -r requirements.txt
python -m ofscraper --ui desktop

# Or via container
docker-compose exec -it ofscraper python -m ofscraper --ui desktop
```

**Desktop UI Features:**
- **Home Tab**: Configure API key, profile URLs, and download settings
- **Progress Tab**: Real-time progress tracking with logs
- **Results Tab**: Tabular view of downloaded content
- **Settings Dialog**: Advanced configuration options

### Web Interface (Flask)

Start the web server:

```bash
# Local development
python -m ofscraper --ui web

# Production deployment
docker-compose exec -it ofscraper python -m ofscraper --ui web
```

**Web Interface Access:**
- **Home**: `http://localhost:5000`
- **Progress**: `http://localhost:5000/progress`
- **Results**: `http://localhost:5000/results`
- **Settings**: `http://localhost:5000/settings`

**Web UI Features:**
- Responsive design for mobile/desktop
- Real-time progress updates via Server-Sent Events
- CSV export functionality
- Settings management

## Common Workflows

### 1. Initial Setup Workflow

```bash
# 1. Clone and configure
git clone <repo>
cd OF-Scraper
cp .env.example .env

# 2. Edit .env with your API key
nano .env

# 3. Start container
docker-compose up -d

# 4. Verify health
curl http://localhost:5000/health
```

### 2. Scraping Workflow (Web UI)

1. Access `http://localhost:5000`
2. Enter API key and profile URLs
3. Select actions (download, like, etc.)
4. Configure download folder
5. Click "Start Scraping"
6. Monitor progress on `/progress` page
7. View results on `/results` page

### 3. Scraping Workflow (Desktop UI)

1. Launch desktop UI: `python -m ofscraper --ui desktop`
2. Enter API key in the home tab
3. Add profile URLs
4. Select download folder
5. Click "Start"
6. Monitor progress in the progress tab
7. Export results via CSV

### 4. Batch Processing (Command Line)

```bash
# Interactive container
docker-compose exec -it ofscraper ofscraper --username ALL --posts all

# Single run
docker run --rm \
  -e OF_API_KEY=your_key \
  -v $(pwd)/data:/app/data \
  of-scraper:latest \
  ofscraper --username profile1,profile2 --posts paid
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Container Won't Start

**Symptoms:** Container exits immediately with error code 1

**Solutions:**
```bash
# Check logs
docker-compose logs of-scraper

# Verify environment variables
docker-compose config

# Check permissions
ls -la data/ config/
```

#### 2. API Key Issues

**Symptoms:** Authentication failures, empty results

**Solutions:**
```bash
# Verify API key
docker-compose exec -it ofscraper env | grep OF_API_KEY

# Test API connectivity
docker-compose exec -it ofscraper python -c "import requests; print(requests.get('https://api.example.com/verify', headers={'Authorization': 'Bearer YOUR_KEY'}).status_code)"
```

#### 3. Permission Issues

**Symptoms:** Permission denied errors, files not writable

**Solutions:**
```bash
# Check container user
docker-compose exec -it ofscraper id

# Fix permissions
sudo chown -R 1001:1001 data/ config/

# Use host user mapping
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)
docker-compose up -d
```

#### 4. Health Check Failures

**Symptoms:** Container marked as unhealthy

**Solutions:**
```bash
# Check health status
docker-compose ps

# Test health endpoint
docker-compose exec -it ofscraper curl -f http://localhost:5000/health

# Restart with health check disabled
docker-compose up -d --no-healthcheck
```

### Log Interpretation

#### Container Logs
```bash
# View all logs
docker-compose logs -f

# Filter by service
docker-compose logs -f of-scraper

# Search for errors
docker-compose logs of-scraper | grep -i error
```

#### Application Logs
- **Location**: `/app/logs/` inside container
- **Level**: DEBUG, INFO, WARNING, ERROR
- **Format**: JSON structured logging

### Performance Tuning

#### Memory Optimization
```yaml
services:
  of-scraper:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

#### CPU Limits
```yaml
services:
  of-scraper:
    deploy:
      resources:
        limits:
          cpus: '2.0'
```

## Health Checks & Monitoring

### Health Check Configuration

The container includes a built-in health check:
- **Endpoint**: `http://localhost:5000/health`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3 attempts

### Custom Health Monitoring

```bash
# Manual health check
curl -f http://localhost:5000/health || echo "Unhealthy"

# Monitor with watch
watch -n 5 'curl -s http://localhost:5000/health || echo "DOWN"'

# Docker health status
docker inspect --format='{{.State.Health.Status}}' ofscraper
```

### Monitoring Scripts

Create a monitoring script `monitor.sh`:

```bash
#!/bin/bash
while true; do
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        echo "$(date): Healthy"
    else
        echo "$(date): Unhealthy - restarting"
        docker-compose restart of-scraper
    fi
    sleep 60
done
```

## Security Considerations

1. **Never commit API keys** to version control
2. **Use non-root user** (already configured)
3. **Limit container resources** to prevent abuse
4. **Regular security updates**:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

## Advanced Configuration

### Custom Entrypoint Scripts

Mount custom scripts:
```yaml
services:
  of-scraper:
    volumes:
      - ./custom-entrypoint.sh:/usr/local/bin/entry/custom.sh
```

### Environment-Specific Configurations

#### Development
```yaml
services:
  of-scraper:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    volumes:
      - ./:/app
```

#### Production
```yaml
services:
  of-scraper:
    restart: unless-stopped
    environment:
      - LOG_LEVEL=INFO
    deploy:
      replicas: 1
```

## Support and Resources

- **Documentation**: Check `/docs` directory
- **Issues**: GitHub Issues page
- **Discussions**: GitHub Discussions
- **Logs**: Always include container logs when reporting issues

---

**Last Updated**: August 16, 2025
**Version**: 1.0.0