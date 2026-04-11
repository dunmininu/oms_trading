# Research Note: Kronos AI (Tsinghua University)

## Overview

Kronos is an open-source **Foundation Model for Financial Time Series**, released by researchers at Tsinghua University. Unlike traditional price prediction models that focus on a single asset, Kronos is trained on a massive corpus of multi-asset candlestick (OHLCV) data, treating market movements as a "language."

## Key Capabilities

1. **Foundational Embeddings**: Instead of just using raw RSI or Z-Scores, Kronos produces high-dimensional embeddings that capture the "context" of a market regime.
2. **Cross-Asset Intelligence**: It can transfer knowledge from highly liquid markets (like Forex) to improve predictions on less liquid ones (like specific Synthetics).
3. **Zero-Shot Forecasting**: The model can perform reasonably well on new instruments without prior training by recognizing universal patterns of price action (sweeps, gaps, etc.).

## Application to our OMS Trading Bot

### 1. Enhanced Feature Engineering

* We can replace or augment our current `MLStrategyService.extract_features` with Kronos embeddings.

- **Current**: 7-10 manual indicators (RSI, ATR, etc.).
- **Kronos-Enhanced**: 128+ dimensional latent vector capturing market "vibes."

### 2. Regime Detection

Kronos is exceptionally good at identifying **Structural Market Shifts** (e.g., from Mean Reversion to Momentum). This would allow our bot to stop trading ICT FVG setups during high-volatility trend transitions where they often fail.

### 3. Synthetic Data Quality

We can use Kronos to generate more realistic backtest data. Our current `run_backtest` command uses simple random walks; Kronos can generate data that respects institutional order flow dynamics.

## Integration Roadmap

> [!IMPORTANT]
> The Kronos weights are released for research. Integrating them into our Django backend would require a dedicated Python environment with PyTorch/Transformers.

1. **Phase 1 (Analysis)**: Run our historical data through Kronos to see if its identified "regimes" correlate with our ICT signal success rates.
2. **Phase 2 (Ensemble)**: Use Kronos's confidence score as an additional "C" confluence factor in our `GradingService`.
3. **Phase 3 (Full Integration)**: Replace the current XGBoost model with a fine-tuned Kronos adapter.

---

*Reference: [Kronos: A Foundation Model for the Language of Financial Markets](https://github.com/shiyu-coder/Kronos)*
