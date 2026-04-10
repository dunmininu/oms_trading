# Native Local Setup Guide (Non-Docker)

This guide walks you through setting up the OMS Trading project directly on your macOS environment. This is often faster for development and avoids common Docker for Mac I/O performance issues.

## 1. Prerequisites

### Homebrew Dependencies
You will need PostgreSQL and Redis. If you don't have Homebrew, install it from [brew.sh](https://brew.sh).

```bash
# Install core services
brew install postgresql@15
brew install redis
brew install pyenv  # Recommended for managing Python versions

# Start the services
brew services start postgresql@15
brew services start redis
```

### Python 3.12
The project is optimized for Python 3.12.
```bash
pyenv install 3.12.0
pyenv global 3.12.0
```

---

## 2. Environment Setup

### Virtual Environment
```bash
# From the project root
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies (development mode)
make dev-install
```

### Configure `.env`
Copy the template and update the connection strings.
```bash
cp .env.example .env
```

**IMPORTANT**: Edit your `.env` to use the default local ports:
```env
# Local settings (standard ports)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/oms_trading_dev
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# Interactive Brokers (Running on your Mac, not in Docker)
IB_HOST=127.0.0.1
IB_PORT=7497
```

---

## 3. Database Initialization

```bash
# Create the database (if not already exists)
createdb oms_trading_dev

# Run migrations
make migrate

# Create your admin user
make superuser
```

---

## 4. Running the Application

Since this is a multi-process system, you will need multiple terminal tabs or a process manager.

### Tab 1: Web Server
```bash
make dev
```

### Tab 2: Celery Worker
```bash
make dev-worker
```

### Tab 3: Celery Beat (Scheduler)
```bash
make dev-beat
```

### Tab 4: Flower (Monitoring)
```bash
make dev-flower
```

---

## 5. Troubleshooting

### Port Conflicts
If you see `Address already in use`, make sure your Docker containers are stopped:
```bash
make docker-down
```

### IB Gateway
To trade, you must have the **IB Gateway** or **TWS** application running on your Mac and logged into your Paper/Live account. Ensure "Enable ActiveX and Socket Clients" is checked in the app's settings.
