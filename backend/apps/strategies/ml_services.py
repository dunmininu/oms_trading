"""
Machine Learning services for trade setup prediction.
"""

import logging
import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.ensemble import RandomForestClassifier
from django.conf import settings

from apps.marketdata.models import HistoricalData
from apps.oms.models import Instrument

logger = logging.getLogger(__name__)

class MLStrategyService:
    """Service for training and inference using Random Forest."""

    MODEL_DIR = os.path.join(settings.BASE_DIR, 'ml_models')

    @classmethod
    def get_model_path(cls, symbol: str):
        if not os.path.exists(cls.MODEL_DIR):
            os.makedirs(cls.MODEL_DIR)
        return os.path.join(cls.MODEL_DIR, f'rf_{symbol.lower()}.joblib')

    @classmethod
    def extract_features(cls, instrument: Instrument, interval: str) -> Optional[pd.DataFrame]:
        """Extract features for the model: RSI, Z-Score, Volatility, Bar Body/Wick ratios."""
        bars = HistoricalData.objects.filter(
            instrument=instrument,
            interval=interval,
            data_type='OHLC'
        ).order_by('start_time')

        if bars.count() < 50:
            return None

        df = pd.DataFrame(list(bars.values(
            'open_price', 'high_price', 'low_price', 'close_price', 'volume'
        )))

        # Convert to float
        for col in ['open_price', 'high_price', 'low_price', 'close_price']:
            df[col] = df[col].astype(float)

        # Technical Indicators
        df['rsi'] = cls._calc_rsi(df['close_price'])
        df['z_score'] = (df['close_price'] - df['close_price'].rolling(20).mean()) / df['close_price'].rolling(20).std()
        df['volatility'] = df['close_price'].pct_change().rolling(20).std()

        # ICT-lite features
        df['body_size'] = abs(df['close_price'] - df['open_price'])
        df['upper_wick'] = df['high_price'] - df.apply(lambda r: max(r['open_price'], r['close_price']), axis=1)
        df['lower_wick'] = df.apply(lambda r: min(r['open_price'], r['close_price']), axis=1) - df['low_price']

        return df.dropna()

    @classmethod
    def predict_setup(cls, instrument: Instrument, interval: str) -> Dict[str, Any]:
        """Predict the probability of a successful 1:2 RR trade."""
        features_df = cls.extract_features(instrument, interval)
        if features_df is None or features_df.empty:
            return {'probability': 0.5, 'confidence': 'LOW'}

        model_path = cls.get_model_path(instrument.symbol)
        if not os.path.exists(model_path):
            # Return neutral if no model trained yet
            return {'probability': 0.5, 'confidence': 'NO_MODEL'}

        model = joblib.load(model_path)

        # Take the most recent feature row
        latest_features = features_df.iloc[-1][['rsi', 'z_score', 'volatility', 'body_size', 'upper_wick', 'lower_wick']].values.reshape(1, -1)

        probs = model.predict_proba(latest_features)[0]
        # Assuming class 1 is "Target Hit"
        prob_success = probs[1] if len(probs) > 1 else 0.5

        return {
            'probability': float(prob_success),
            'confidence': 'HIGH' if prob_success > 0.7 or prob_success < 0.3 else 'MEDIUM'
        }

    @classmethod
    def train_model(cls, instrument: Instrument, interval: str):
        """Train a model on historical outcomes."""
        df = cls.extract_features(instrument, interval)
        if df is None or len(df) < 100:
            logger.warning(f"Not enough data to train model for {instrument.symbol}")
            return

        # Simple Labelling: if price moves +2% before -1% (approx 1:2 RR aim)
        # Note: In production, use actual ATR-based stops/targets
        df['target'] = 0
        prices = df['close_price'].values
        for i in range(len(prices) - 20):
            entry = prices[i]
            hit = False
            for j in range(i + 1, i + 20):
                change = (prices[j] - entry) / entry
                if change > 0.02: # +2% Target hit
                    df.at[df.index[i], 'target'] = 1
                    hit = True
                    break
                if change < -0.01: # -1% Stop hit
                    break

        X = df[['rsi', 'z_score', 'volatility', 'body_size', 'upper_wick', 'lower_wick']]
        y = df['target']

        model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        model.fit(X, y)

        joblib.dump(model, cls.get_model_path(instrument.symbol))
        logger.info(f"Model trained and saved for {instrument.symbol}")

    @staticmethod
    def _calc_rsi(prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
