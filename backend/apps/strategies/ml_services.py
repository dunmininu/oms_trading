"""
Machine Learning services using XGBoost for trade setup prediction.
"""

import logging
import os
from typing import Any

import joblib
import pandas as pd
import xgboost as xgb
from django.conf import settings

from apps.marketdata.models import HistoricalData
from apps.oms.models import Instrument

from .models import LearningLabel, MLTrainingLog

logger = logging.getLogger(__name__)


class MLStrategyService:
    """Service for training and inference using XGBoost."""

    MODEL_DIR = os.path.join(settings.BASE_DIR, "ml_models")

    @classmethod
    def _log_training(cls, symbol: str, message: str, level: str = "INFO"):
        """Write a log entry to the database for real-time monitoring."""
        MLTrainingLog.objects.create(symbol=symbol, message=message, level=level)
        logger.info(f"[ML-TRAIN][{symbol}] {message}")

    @classmethod
    def harvest_outcome(
        cls,
        symbol: str,
        features: dict,
        outcome: str,
        pnl: float = 0,
        setup_type: str = "UNKNOWN",
    ):
        """Save a trade/signal outcome for future model calibration."""
        LearningLabel.objects.create(
            symbol=symbol,
            features_json=features,
            outcome=outcome,
            pnl=pnl,
            setup_type=setup_type,
        )

    @classmethod
    def get_model_path(cls, symbol: str):
        if not os.path.exists(cls.MODEL_DIR):
            os.makedirs(cls.MODEL_DIR)
        return os.path.join(cls.MODEL_DIR, f"xgb_{symbol.lower()}.joblib")

    @classmethod
    def extract_features(
        cls, instrument: Instrument, interval: str
    ) -> pd.DataFrame | None:
        """Enhanced feature extraction: RSI, Z-Score, ATR (Volatility), Volume Profile, Wick ratios."""
        symbol = instrument.symbol

        # Mapping for inconsistent interval strings
        interval_map = {
            "1 min": "1_MINUTE",
            "15 mins": "15_MINUTE",
            "1 hour": "1_HOUR",
            "4 hours": "4_HOUR",
            "1 day": "1_DAY",
        }
        mapped_interval = interval_map.get(interval, interval)

        bars = HistoricalData.objects.filter(
            instrument=instrument, interval=mapped_interval, data_type="OHLC"
        ).order_by("start_time")

        count = bars.count()
        if count < 100:
            cls._log_training(
                symbol,
                f"Insufficient data: found {count} bars for {mapped_interval} (need 100).",
                "WARNING",
            )
            return None

        df = pd.DataFrame(
            list(
                bars.values(
                    "open_price", "high_price", "low_price", "close_price", "volume"
                )
            )
        )

        # Convert to float
        for col in ["open_price", "high_price", "low_price", "close_price"]:
            df[col] = df[col].astype(float)

        # Technical Indicators
        df["rsi"] = cls._calc_rsi(df["close_price"])
        df["z_score"] = (df["close_price"] - df["close_price"].rolling(20).mean()) / df[
            "close_price"
        ].rolling(20).std()

        # ATR (Volatility)
        high_low = df["high_price"] - df["low_price"]
        high_cp = abs(df["high_price"] - df["close_price"].shift())
        low_cp = abs(df["low_price"] - df["close_price"].shift())
        df["tr"] = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
        df["atr"] = df["tr"].rolling(14).mean()

        # Volume Profile (Simplified) - Handle 0 volume in Synthetics
        df["vol_ma"] = df["volume"].rolling(20).mean()
        df["vol_ratio"] = df.apply(
            lambda r: r["volume"] / r["vol_ma"] if r["vol_ma"] > 0 else 1.0, axis=1
        )

        # Candlestick characteristics
        df["body_size"] = abs(df["close_price"] - df["open_price"])
        df["upper_wick"] = df["high_price"] - df.apply(
            lambda r: max(r["open_price"], r["close_price"]), axis=1
        )
        df["lower_wick"] = (
            df.apply(lambda r: min(r["open_price"], r["close_price"]), axis=1)
            - df["low_price"]
        )

        return df.dropna()

    @classmethod
    def predict_setup(cls, instrument: Instrument, interval: str) -> dict[str, Any]:
        """Predict the probability of a successful 1:2 RR trade using XGBoost."""
        features_df = cls.extract_features(instrument, interval)
        if features_df is None or features_df.empty:
            return {"probability": 0.5, "confidence": "LOW"}

        model_path = cls.get_model_path(instrument.symbol)
        if not os.path.exists(model_path):
            return {"probability": 0.5, "confidence": "NO_MODEL"}

        model = joblib.load(model_path)

        feature_cols = [
            "rsi",
            "z_score",
            "atr",
            "vol_ratio",
            "body_size",
            "upper_wick",
            "lower_wick",
        ]
        latest_features = features_df.iloc[-1][feature_cols].values.reshape(1, -1)

        # XGBoost prediction
        prob_success = model.predict_proba(latest_features)[0][1]

        return {
            "probability": float(prob_success),
            "confidence": (
                "HIGH" if prob_success > 0.75 or prob_success < 0.25 else "MEDIUM"
            ),
        }

    @classmethod
    def train_model(cls, instrument: Instrument, interval: str):
        """Train an XGBoost model on historical outcomes."""
        df = cls.extract_features(instrument, interval)
        if df is None or len(df) < 100:
            cls._log_training(
                instrument.symbol,
                f"Training aborted: Insufficient data samples (found {len(df) if df is not None else 0}, need 100).",
                level="WARNING",
            )
            return

        # Target: Price moves +2 ATR before -1 ATR (Dynamic 1:2 RR)
        df["target"] = 0
        prices = df["close_price"].values
        atrs = df["atr"].values

        for i in range(len(prices) - 30):
            entry = prices[i]
            atr = atrs[i]
            target_price = entry + (2 * atr)
            stop_price = entry - atr

            for j in range(i + 1, i + 30):
                if prices[j] >= target_price:
                    df.at[df.index[i], "target"] = 1
                    break
                if prices[j] <= stop_price:
                    break

        feature_cols = [
            "rsi",
            "z_score",
            "atr",
            "vol_ratio",
            "body_size",
            "upper_wick",
            "lower_wick",
        ]
        X = df[feature_cols]
        y = df["target"]

        # Integrate Self-Learned Labels if any exist
        harvested = LearningLabel.objects.filter(symbol=instrument.symbol).order_by(
            "-created_at"
        )[:1000]
        if harvested.exists():
            cls._log_training(
                instrument.symbol,
                f"Integrating {harvested.count()} self-learned outcomes into training pool.",
            )
            h_features = []
            h_labels = []
            for label in harvested:
                # Ensure feature keys match model expectations
                feat = [label.features_json.get(c, 0) for c in feature_cols]
                h_features.append(feat)
                h_labels.append(1 if label.outcome == "WIN" else 0)

            X = pd.concat(
                [X, pd.DataFrame(h_features, columns=feature_cols)], ignore_index=True
            )
            y = pd.concat([y, pd.Series(h_labels)], ignore_index=True)

        cls._log_training(
            instrument.symbol, f"Igniting XGBoost Engine with {len(X)} samples..."
        )

        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
        )
        model.fit(X, y)

        joblib.dump(model, cls.get_model_path(instrument.symbol))
        cls._log_training(
            instrument.symbol,
            "Model successfully locked in. Precision optimized for 1:2 RR.",
            level="SUCCESS",
        )

    @staticmethod
    def _calc_rsi(prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @classmethod
    def predict_success(
        cls, setup: dict[str, Any], quant_data: dict[str, Any]
    ) -> float:
        """Heuristic-based probability for backtesting when a trained model is unavailable."""
        # Baseline probability for detected setup
        prob = 0.55

        # Confluence: Align with Market Regime
        if (
            setup["type"] == "BULLISH"
            and quant_data["regime"] == "OVERSOLD"
            or setup["type"] == "BEARISH"
            and quant_data["regime"] == "OVERBOUGHT"
        ):
            prob += 0.15

        # Confluence: Mean reversion alignment (Strong Z-Score)
        if abs(quant_data["z_score"]) > 1.5:
            prob += 0.1

        # Confluence: ATR Volatility presence
        if quant_data.get("atr", 0) > 0:
            prob += 0.05

        return min(max(prob, 0.0), 1.0)
