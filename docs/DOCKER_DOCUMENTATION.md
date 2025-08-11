# OMS Trading System - Docker Documentation

## Overview
This document provides comprehensive information about the Docker setup for the OMS Trading System, including development, staging, and production configurations.

## Architecture

### Service Overview
The OMS Trading System consists of the following Docker services:

1. **PostgreSQL** - Primary database
2. **Redis** - Cache and message broker
3. **IB Gateway** - Interactive Brokers connection
4. **Web** - Django application
5. **Celery Worker** - Background task processing
6. **Celery Beat** - Scheduled task scheduler
7. **Flower** - Celery monitoring
8. **Nginx** - Load balancer (production)
9. **Prometheus** - Metrics collection (monitoring)
10. **Grafana** - Metrics visualization (monitoring)

## Quick Start

### Prerequisites
- Docker Desktop 20.10+
- Docker Compose 2.0+
- At least 8GB RAM available
- Ports 8000, 5433, 6379, 7497 available

### Development Environment
```bash
# Clone the repository
git clone <repository-url>
cd oms_trading

# Copy environment file
cp .env.example .env

# Start all services
make docker-up

# Or manually
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f web
```

### Environment Variables
Create a `.env` file with the following variables:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
API_KEY_SECRET=your-api-key-secret

# Database
POSTGRES_DB=oms_trading_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Interactive Brokers
IB_USERNAME=your-ib-username
IB_PASSWORD=your-ib-password
IB_ACCOUNT=your-ib-account

# Monitoring
FLOWER_USER=admin
FLOWER_PASSWORD=flower123
GRAFANA_USER=admin
GRAFANA_PASSWORD=grafana123

# VNC Access
VNC_PASSWORD=oms123
```

## Service Details

### 1. PostgreSQL Database
```yaml
postgres:
  image: postgres:15-alpine
  container_name: oms_postgres
  environment:
    POSTGRES_DB: oms_trading_dev
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
  ports:
    - "5433:5432"  # Mapped to avoid conflicts
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./infra/scripts/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh:ro
```

**Features:**
- Alpine-based for smaller image size
- Health checks with `pg_isready`
- Persistent data volume
- Custom initialization script
- UTF-8 encoding with proper locale

**Access:**
```bash
# Connect from host
psql -h localhost -p 5433 -U postgres -d oms_trading_dev

# Connect from container
docker exec -it oms_postgres psql -U postgres -d oms_trading_dev
```

### 2. Redis Cache & Message Broker
```yaml
redis:
  image: redis:7-alpine
  container_name: oms_redis
  command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
```

**Features:**
- AOF persistence for data durability
- Memory limit with LRU eviction
- Health checks with ping
- Optimized for caching and message queuing

**Usage:**
```bash
# Redis CLI
docker exec -it oms_redis redis-cli

# Monitor
docker exec -it oms_redis redis-cli monitor
```

### 3. Interactive Brokers Gateway
```yaml
ib-gateway:
  image: ghcr.io/gnzsnz/ib-gateway:latest
  platform: linux/amd64
  container_name: oms_ib_gateway
  environment:
    TWS_USERID: ${IB_USERNAME:-edemo}
    TWS_PASSWORD: ${IB_PASSWORD:-demouser}
    TRADING_MODE: paper
    VNC_SERVER_PASSWORD: ${VNC_PASSWORD:-oms123}
  ports:
    - "7497:7497"  # IB API port
    - "4001:4001"  # TWS port
    - "5900:5900"  # VNC port
```

**Features:**
- Paper trading mode for development
- VNC access for GUI management
- Health checks on API port
- Configurable credentials

**VNC Access:**
```bash
# Connect with VNC client
vncviewer localhost:5900
# Password: oms123 (or VNC_PASSWORD from .env)
```

### 4. Django Web Application
```yaml
web:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: oms_web
  environment:
    DJANGO_SETTINGS_MODULE: apps.core.settings.dev
    DATABASE_URL: postgresql://postgres:postgres@postgres:5432/oms_trading_dev
    REDIS_URL: redis://redis:6379/0
    CELERY_BROKER_URL: redis://redis:6379/1
  ports:
    - "8000:8000"
  volumes:
    - ./backend:/app/backend
    - ./logs:/app/logs
    - ./media:/app/media
```

**Features:**
- Multi-stage Docker build
- Development volume mounts for hot reloading
- Health checks with curl
- Environment-specific settings

**Development Workflow:**
```bash
# View logs
docker-compose logs -f web

# Execute commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Shell access
docker-compose exec web python manage.py shell
```

### 5. Celery Background Tasks
```yaml
celery-worker:
  build:
    context: .
    dockerfile: Dockerfile
  command: celery -A apps.core worker --loglevel=info --concurrency=4
  environment:
    CELERY_BROKER_URL: redis://redis:6379/1
    C_FORCE_ROOT: "true"
```

**Features:**
- 4 concurrent workers
- Redis as message broker
- Automatic restart on failure
- Root user for system operations

**Monitoring:**
```bash
# Check worker status
docker-compose exec celery-worker celery -A apps.core inspect active

# View worker logs
docker-compose logs -f celery-worker
```

### 6. Celery Beat Scheduler
```yaml
celery-beat:
  build:
    context: .
    dockerfile: Dockerfile
  command: celery -A apps.core beat --scheduler=django_celery_beat.schedulers:DatabaseScheduler
```

**Features:**
- Database-backed scheduler
- Persistent task schedules
- Automatic restart on failure

### 7. Flower Monitoring
```yaml
flower:
  build:
    context: .
    dockerfile: Dockerfile
  command: celery -A apps.core flower --port=5555
  ports:
    - "5555:5555"
  environment:
    FLOWER_BASIC_AUTH: ${FLOWER_USER:-admin}:${FLOWER_PASSWORD:-flower123}
```

**Features:**
- Web-based Celery monitoring
- Basic authentication
- Real-time task monitoring
- Worker statistics

**Access:**
- URL: http://localhost:5555
- Username: admin (or FLOWER_USER)
- Password: flower123 (or FLOWER_PASSWORD)

## Production Configuration

### Nginx Load Balancer
```yaml
nginx:
  image: nginx:alpine
  container_name: oms_nginx
  volumes:
    - ./infra/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./staticfiles:/staticfiles:ro
    - ./media:/media:ro
  ports:
    - "80:80"
    - "443:443"
  profiles:
    - production
```

**Features:**
- Static file serving
- Load balancing
- SSL termination (configure in nginx.conf)
- Production profile activation

### Monitoring Stack
```yaml
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
  ports:
    - "9090:9090"
  profiles:
    - monitoring

grafana:
  image: grafana/grafana:latest
  environment:
    GF_SECURITY_ADMIN_USER: ${GRAFANA_USER:-admin}
    GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-grafana123}
  ports:
    - "3000:3000"
  profiles:
    - monitoring
```

**Features:**
- Metrics collection
- Custom dashboards
- Alerting rules
- Monitoring profile activation

## Docker Commands

### Development
```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d postgres redis

# View running services
docker-compose ps

# View service logs
docker-compose logs -f [service_name]

# Execute commands in container
docker-compose exec [service_name] [command]

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Production
```bash
# Start with production profile
docker-compose --profile production up -d

# Start with monitoring
docker-compose --profile monitoring up -d

# Start all profiles
docker-compose --profile production --profile monitoring up -d
```

### Maintenance
```bash
# Rebuild images
docker-compose build --no-cache

# Update services
docker-compose pull
docker-compose up -d

# Clean up unused resources
docker system prune -a

# View resource usage
docker stats
```

## Troubleshooting

### Common Issues

#### 1. Port Conflicts
```bash
# Check what's using a port
lsof -i :8000

# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready -U postgres

# Check logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

#### 3. Redis Connection Issues
```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Check logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

#### 4. IB Gateway Issues
```bash
# Check IB Gateway status
docker-compose exec ib-gateway netstat -an | grep 7497

# Check logs
docker-compose logs ib-gateway

# Restart IB Gateway
docker-compose restart ib-gateway
```

### Performance Tuning

#### 1. Database Performance
```yaml
postgres:
  environment:
    POSTGRES_SHARED_BUFFERS: 256MB
    POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
    POSTGRES_WORK_MEM: 4MB
    POSTGRES_MAINTENANCE_WORK_MEM: 64MB
```

#### 2. Redis Performance
```yaml
redis:
  command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru --save 900 1 --save 300 10 --save 60 10000
```

#### 3. Celery Performance
```yaml
celery-worker:
  command: celery -A apps.core worker --loglevel=info --concurrency=8 --max-tasks-per-child=1000 --prefetch-multiplier=4
```

## Security Considerations

### 1. Environment Variables
- Never commit `.env` files to version control
- Use strong, unique secrets for production
- Rotate secrets regularly
- Use Docker secrets for sensitive data in production

### 2. Network Security
- Services communicate over internal Docker network
- Only necessary ports exposed to host
- Use reverse proxy for external access
- Implement proper authentication

### 3. Container Security
- Use specific image tags (not `latest`)
- Regular security updates
- Minimal base images
- Non-root users where possible

## Monitoring and Logging

### 1. Health Checks
All services include health checks:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health/"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 2. Logging
- Structured logging to stdout/stderr
- Log rotation and retention
- Centralized log collection (ELK stack recommended for production)

### 3. Metrics
- Prometheus metrics collection
- Custom business metrics
- Performance monitoring
- Alerting rules

## Backup and Recovery

### 1. Database Backups
```bash
# Create backup
docker-compose exec postgres pg_dump -U postgres oms_trading_dev > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U postgres oms_trading_dev < backup.sql
```

### 2. Volume Backups
```bash
# Backup volumes
docker run --rm -v oms_trading_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volumes
docker run --rm -v oms_trading_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

## Development Workflow

### 1. Local Development
```bash
# Start services
make docker-up

# Run tests
make test

# Run linting
make lint

# Run migrations
make migrate

# Create superuser
make superuser
```

### 2. Testing
```bash
# Run all tests
docker-compose exec web python manage.py test

# Run specific tests
docker-compose exec web python manage.py test apps.oms.tests

# Run with coverage
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report
```

### 3. Code Quality
```bash
# Run linting
docker-compose exec web ruff check .

# Run type checking
docker-compose exec web mypy .

# Format code
docker-compose exec web black .
```

## Conclusion

This Docker setup provides a robust, scalable foundation for the OMS Trading System. The configuration supports development, staging, and production environments with proper separation of concerns and security measures.

For production deployment, ensure:
- Proper secrets management
- SSL/TLS configuration
- Monitoring and alerting
- Backup and disaster recovery procedures
- Security hardening
- Performance tuning
