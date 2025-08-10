# OMS Trading - Order Management System

A production-grade, multi-tenant Order Management System (OMS) built with Django and designed for Interactive Brokers integration.

## Features

- **Multi-tenant Architecture** - Secure tenant isolation with role-based access control
- **Interactive Brokers Integration** - Real-time trading via TWS/Gateway with ib_insync
- **Order Management** - Complete order lifecycle with state machine and audit trail
- **Risk Management** - Configurable pre-trade risk checks and position limits
- **Market Data** - Real-time market data subscriptions and caching
- **Strategy Framework** - Plugin-based strategy execution with sandboxing
- **Event-Driven Architecture** - Webhook notifications and event bus
- **Production Ready** - Docker deployment, monitoring, and observability

## Architecture

Built with modern Python technologies following senior engineering best practices:

- **Django 5** + **Django Ninja** for APIs with automatic OpenAPI documentation
- **PostgreSQL** for reliable data persistence with ACID compliance
- **Redis** for caching, sessions, and Celery task queue
- **Celery** for asynchronous task processing
- **ib_insync** for Interactive Brokers connectivity
- **Docker** for containerized deployment

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Interactive Brokers account (paper trading supported)
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd oms_trading

# Copy environment template and configure
cp .env.example .env
# Edit .env with your settings

# Install dependencies
make dev-install
```

### 2. Start with Docker (Recommended)

```bash
# Start all services (PostgreSQL, Redis, IB Gateway, Web App, Celery)
make docker-up

# Or start individually
docker compose up -d postgres redis
docker compose up web
```

### 3. Manual Setup (Alternative)

```bash
# Start database and cache
docker compose up -d postgres redis

# Run migrations
make migrate

# Create superuser
make superuser

# Start development server
make dev

# In separate terminals, start Celery services
make dev-worker
make dev-beat
```

### 4. Access the Application

- **Web API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Django Admin**: http://localhost:8000/admin
- **Flower (Celery Monitor)**: http://localhost:5555
- **IB Gateway VNC**: vnc://localhost:5900 (password: oms123)

## Development

### Available Commands

```bash
# Development
make dev              # Start development server
make dev-worker       # Start Celery worker
make dev-beat         # Start Celery beat scheduler
make shell            # Django shell

# Code Quality
make test             # Run tests
make test-cov         # Run tests with coverage
make lint             # Run linting
make format           # Format code
make check-all        # Run all quality checks

# Database
make migrate          # Run migrations
make makemigrations   # Create migrations
make seed-data        # Load sample data

# Docker
make docker-up        # Start all services
make docker-down      # Stop all services
make docker-logs      # View logs
make docker-shell     # Access container shell
```

### Project Structure

```
backend/
├── apps/
│   ├── core/           # Base functionality, settings, middleware
│   ├── accounts/       # Authentication, users, API keys
│   ├── tenants/        # Multi-tenancy support
│   ├── brokers/        # Broker integrations (IB)
│   ├── marketdata/     # Market data management
│   ├── oms/            # Order management system
│   ├── strategies/     # Strategy framework
│   ├── events/         # Event bus and webhooks
│   └── api/            # API configuration
├── libs/
│   ├── ibsdk/          # Enhanced IB SDK wrapper
│   └── shared/         # Shared utilities
├── infra/              # Infrastructure configs
└── tests/              # Test suite
```

## Security

- JWT-based authentication with refresh tokens
- API key authentication for machine-to-machine access
- Role-based permissions with scoped access
- Request rate limiting
- Comprehensive audit logging
- Encrypted sensitive data storage

## Monitoring & Observability

- Structured JSON logging with correlation IDs
- Prometheus metrics for business and system metrics
- Sentry integration for error tracking
- Health check endpoints for Kubernetes
- Celery monitoring with Flower

## Testing

```bash
# Run all tests
make test

# Run specific test types
make test-unit         # Unit tests only
make test-integration  # Integration tests only

# Run with coverage
make test-cov

# Watch mode for development
make test-watch
```

## Deployment

### Docker Production

```bash
# Build production image
docker build -t oms-trading:latest .

# Run with production settings
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Core
SECRET_KEY=your-production-secret
DEBUG=false
ALLOWED_HOSTS=your-domain.com

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Interactive Brokers
IB_HOST=your-ib-gateway-host
IB_PORT=4001
IB_ACCOUNT=your-account-id

# Risk Management
RISK_MAX_POSITION_SIZE=1000000
RISK_MAX_ORDER_SIZE=100000
```

## API Documentation

Interactive API documentation is available at `/api/docs` when running the server.

### Key Endpoints

- `POST /api/v1/auth/login` - Authenticate and get JWT tokens
- `POST /api/v1/orders` - Place new order (idempotent)
- `GET /api/v1/orders` - List orders with filtering
- `POST /api/v1/orders/{id}/cancel` - Cancel order
- `GET /api/v1/positions` - Get current positions
- `GET /api/v1/pnl/today` - Today's P&L summary

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Run linting (`make lint`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Standards

- Follow PEP 8 and use `ruff` for linting
- Maintain 80%+ test coverage
- Add type hints for all functions
- Write docstrings for public APIs
- Use conventional commit messages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is for educational and development purposes. Always test thoroughly in paper trading mode before using with real money. Trading involves risk of loss.

## Support

- Create an issue for bug reports or feature requests
- Check the [documentation](docs/) for detailed guides
- Review the [architecture document](ARCHITECTURE.md) for system design

## Roadmap

- [ ] Additional broker integrations (Alpaca, TD Ameritrade)
- [ ] WebSocket API for real-time updates
- [ ] Advanced strategy backtesting
- [ ] Machine learning integration
- [ ] Mobile app support
- [ ] Advanced reporting and analytics

---

Built with for the trading community


# OMS Trading

Production-grade Order Management System for Interactive Brokers.

## Quick Start

```bash
# Start with Docker
make docker-up

# Or develop locally
make dev-install
make dev
```

## Features

- Real-time order management
- Interactive Brokers integration
- Risk management
- API-first architecture
- Production-ready monitoring

## Documentation

See the full documentation for setup and usage instructions.