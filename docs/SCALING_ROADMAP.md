# Quantitative Bot Scaling & Evolution Roadmap

As a Senior Quant Software Engineer, I have assessed the current architecture and identified the following path for scaling this bot from a retail prototype to a high-concurrency production system.

## 1. Current State Assessment
- **Multi-tenancy**: Core isolation is in place. Multiple users can run their own strategies without interference.
- **Data Model**: SQL-based storage for bars is suitable for low-frequency strategies (15m/4H) but will bottleneck for tick-level data.
- **Execution**: Mocked IB integration allows for safe testing. Asynchronous callbacks are in place for real execution.
- **Intelligence**: Self-learning feedback loop is implemented, allowing the bot to penalize underperforming setups.

## 2. Scaling Roadmap

### Phase 1: Real-Time Performance (Current Focus)
- **Redis TimeSeries**: Move real-time tick and 1-minute bar storage to Redis TimeSeries for sub-millisecond access.
- **Celery Beat**: Distribute setup detection across multiple Celery workers to allow scanning hundreds of pairs simultaneously.

### Phase 2: Intelligence & Advanced Quant
- **ML Integration**: Replace the simple `LearningService` with a Scikit-learn or XGBoost model that uses more features (volatility, volume profile, HTF alignment) to predict trade success.
- **Dynamic Risk**: Implement Kelly Criterion for position sizing based on the historical win probability of the specific setup grade.

### Phase 3: Infrastructure Scaling
- **Kubernetes**: Deploy the Django web app and Celery workers as auto-scaling pods.
- **IB Gateway Cluster**: Use multiple IB Gateway instances in a load-balanced pool to handle higher request rates and avoid client ID collisions.
- **Database Partitioning**: Implement PostgreSQL table partitioning for `HistoricalData` and `Execution` logs to maintain query performance as data grows into millions of rows.

## 3. High-Concurrency Multi-User Support
The system is designed so that:
1. Each **Tenant** has their own **BrokerConnection**.
2. Each **StrategyRun** is linked to a specific user and tenant.
3. **Isolation Check**: All services require a `tenant` context. To further harden this, we should implement **Django Row Level Security (RLS)** or a dedicated multi-tenant middleware that automatically injects `tenant_id` into every query.

## 4. Stability & Self-Healing
- **Automatic Reconnection**: The `IBClient` should be enhanced with exponential backoff for connection drops.
- **Health Monitoring**: Prometheus metrics for "Signal Latency" and "Order Fill Time" to detect slippage or connectivity issues in real-time.
