# Sanusi OMS Bot Manual

Welcome to the **Sanusi OMS Bot**, a professional-grade multi-tenant quantitative trading system designed for institutional-level precision in the retail market. This system integrates **ICT (Inner Circle Trader)** methodologies with **Advanced Quantitative models** and **Machine Learning** to identify and execute high-probability trade setups.

---

## 1. System Overview

### Core Philosophy: "The Confluence of Intelligence"
The bot operates by looking for a three-layer confluence before risking capital:
1.  **ICT Signals**: Fair Value Gaps (FVG) and Liquidity Sweeps on 15-minute and 4-hour timeframes.
2.  **Quant Regime**: RSI-based momentum and Z-Score mean-reversion analysis.
3.  **ML Confidence**: An XGBoost classifier that predicts the probability of a setup reaching a 1:2 Risk-Reward (RR) target based on historical market behavior.

### Target Instruments
-   **Forex**: GBPJPY (Great British Pound / Japanese Yen)
-   **Crypto**: BTCUSD (Bitcoin / US Dollar)
-   **Synthetic Indices**: VIX25 and VIX100 (Volatility Indices via Deriv)

---

## 2. Setup & Configuration

### Prerequisites
-   Docker and Docker Compose installed.
-   An Interactive Brokers (IB) account (Paper or Live).
-   A Deriv API Token (for VIX trading).

### Installation
1.  Clone the repository.
2.  Set up your environment variables in `.env` (refer to `.env.example`).
3.  Start the infrastructure:
    ```bash
    make docker-up
    ```
4.  Initialize the database and brokers:
    ```bash
    make migrate
    python backend/manage.py seed_brokers
    ```

### Broker Integration
-   **Interactive Brokers**: Ensure IB Gateway or TWS is running on your host machine. Use `host.docker.internal` as the host in your `.env` if running inside Docker.
-   **Deriv**: Add your API token to the `BrokerConnection` record for Deriv in the Django Admin.

---

## 3. The Strategy Engine

### Setup Grading System
Every detected signal is assigned a grade from **A+ to D-**:
-   **A+**: High confluence (ICT + Quant + HTF Alignment + High ML Probability).
-   **B**: Good confluence (ICT + Quant Confirmation).
-   **C**: Basic signal (ICT only).
-   **D-**: Weak setup (Filtered out by the risk engine).

### Self-Learning Mechanism
The bot tracks the **SetupPerformance** of every trade. If a specific setup (e.g., "FVG Bullish on 15m") consistently loses, the `LearningService` will automatically penalize that setup's score, effectively "learning" to avoid traps in certain market regimes.

---

## 4. Risk Management

### The 10% Rule
The bot is hard-coded to never risk more than **10% of the account balance** on a single trade scale.

### Dynamic Position Sizing (Kelly Criterion)
The bot uses a **Half-Kelly** model to determine the exact quantity to trade:
-   It uses the **XGBoost win probability** to calculate the optimal mathematical stake.
-   If the ML model is 70% confident, the stake increases (up to the 10% cap).
-   If confidence is low, the stake is reduced or the trade is blocked.

### Trade Limits
-   **A+ Setup**: Max 5 simultaneous trades per pair.
-   **B Setup**: Max 3 simultaneous trades per pair.
-   **C Setup**: Max 1 trade per pair.

---

## 5. Trading Command Center (UI)

The bot provides a real-time dashboard accessible via the **Django Admin**:
1.  Login to `http://localhost:8000/admin`.
2.  Navigate to **Strategies** -> **Strategy Runs** -> **Dashboard**.
3.  **Active Positions**: Monitor your live exposure and unrealized PnL.
4.  **Strategy Performance**: View which setup types are currently "winning" according to the self-learning model.
5.  **Recent Orders**: A real-time audit trail of every buy/sell action.

---

## 6. Operational Commands

### retrain ML Models
To update the XGBoost models with the latest market data:
```bash
python backend/manage.py train_trading_model
```

### Run System Verification
To perform a safe, end-to-end "Major Test" using mocked execution:
```bash
python backend/manage.py run_major_verification
```

---

## 7. Scaling for the Future
The system is built on an **Event-Driven Architecture**:
-   **Redis Cache**: Stores ticks with sub-millisecond latency.
-   **Celery Workers**: Distribute the scanning workload across multiple pairs simultaneously.
-   **Multi-Tenancy**: Settings and trades are strictly isolated per user/tenant.

---
**Disclaimer**: Trading involves significant risk of loss. This bot is for educational and developmental purposes. Always test strategies thoroughly in a paper trading environment before risking real capital.
