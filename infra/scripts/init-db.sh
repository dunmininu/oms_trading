#!/bin/bash
set -e

# Initialize PostgreSQL database for OMS Trading
echo "Initializing OMS Trading database..."

# Create additional databases if needed
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create test database
    CREATE DATABASE oms_trading_test;
    
    -- Create extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
    CREATE EXTENSION IF NOT EXISTS "btree_gin";
    
    -- Grant permissions
    GRANT ALL PRIVILEGES ON DATABASE oms_trading_dev TO postgres;
    GRANT ALL PRIVILEGES ON DATABASE oms_trading_test TO postgres;
    
    \echo 'OMS Trading databases initialized successfully!'
EOSQL
