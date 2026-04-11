# ML Trading Model Guide

This guide outlines the machine learning architecture and training techniques implemented to assist the trading bot in achieving a consistent 1:2 Risk-Reward ratio.

## 1. Model Architecture
<<<<<<< HEAD
- **Algorithm**: Random Forest Classifier (100 estimators, max depth 5).
- **Goal**: Predict the probability that a setup will reach a +2% target before hitting a -1% stop.
- **Features**:
=======

- **Algorithm**: Random Forest Classifier (100 estimators, max depth 5).
- **Goal**: Predict the probability that a setup will reach a +2% target before hitting a -1% stop.
- **Features**:
>>>>>>> origin/main
  - Momentum (RSI)
  - Mean Reversion (Z-Score)
  - Volatility (Standard Deviation of returns)
  - Bar Characteristics (Body size, Upper wick, Lower wick ratios)

## 2. Recommended Training Techniques

### Walk-Forward Optimization
<<<<<<< HEAD
Instead of a simple train-test split, we recommend **Walk-Forward Optimization**:
=======

Instead of a simple train-test split, we recommend **Walk-Forward Optimization**:

>>>>>>> origin/main
1. Train on months 1-6, test on month 7.
2. Train on months 2-7, test on month 8.
3. This simulates how the model will perform in production as it adapts to new market regimes.

### Feature Engineering for ICT
<<<<<<< HEAD
To improve performance, consider adding:
=======

To improve performance, consider adding:

>>>>>>> origin/main
- **Displacement**: Measuring the speed of price movement after an FVG.
- **Liquidity Voids**: Quantifying the volume gaps in specific price areas.
- **Time of Day**: Boolean features for London/New York sessions.

### Handling Imbalanced Data
<<<<<<< HEAD
Winning 1:2 RR trades are often rarer than losers. Use **SMOTE (Synthetic Minority Over-sampling Technique)** or adjust the `class_weight` parameter in the Random Forest to ensure the model doesn't just predict "Loss" every time.

## 3. Operations
### Training a new model
Run the following management command to retrain models on your latest historical data:
=======

Winning 1:2 RR trades are often rarer than losers. Use **SMOTE (Synthetic Minority Over-sampling Technique)** or adjust the `class_weight` parameter in the Random Forest to ensure the model doesn't just predict "Loss" every time.

## 3. Operations

### Training a new model

Run the following management command to retrain models on your latest historical data:

>>>>>>> origin/main
```bash
python backend/manage.py train_trading_model
```

### Inference
<<<<<<< HEAD
The `GradingService` automatically uses the trained models. If no model is found, it defaults to a neutral confidence.
- **Confidence > 0.7**: Boosts setup grade.
- **Confidence < 0.3**: Can be used to filter out low-probability "traps".
=======

The `GradingService` automatically uses the trained models. If no model is found, it defaults to a neutral confidence.

- **Confidence > 0.7**: Boosts setup grade.
- **Confidence < 0.3**: Can be used to filter out low-probability "traps".


##### TODO

We should look into Kronos AI ML model for trading
>>>>>>> origin/main
