"""
Interaction-based product recommender.

Cold start (no history): falls back to distance + nutriscore + ecoscore ranking.
Warm: trains a LogisticRegression on session click/chat interactions and re-ranks.
"""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

SCORE_MAP = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, None: 3}


def _feature_vector(p: dict) -> list[float]:
    return [
        p.get("km", 500),
        SCORE_MAP.get(p.get("ns"), 3),
        SCORE_MAP.get(p.get("es"), 3),
        p.get("co2", 0.0),
    ]


class Recommender:
    def __init__(self):
        self._model: LogisticRegression | None = None
        self._scaler = StandardScaler()

    def train(self, interactions_df, products: list[dict]) -> None:
        """Train on a pandas DataFrame of logged interactions."""
        clicked = set(
            interactions_df[
                interactions_df["action"].isin(["click", "chat"])
                & interactions_df["product_id"].notna()
            ]["product_id"].astype(int)
        )

        X, y = [], []
        for p in products:
            X.append(_feature_vector(p))
            y.append(1 if p["id"] in clicked else 0)

        if len(set(y)) < 2:
            return  # not enough signal yet

        X = self._scaler.fit_transform(X)
        self._model = LogisticRegression(max_iter=500)
        self._model.fit(X, y)

    def rank(self, session_id: str, products: list[dict], n: int = 5) -> list[dict]:
        """Return top-n products. Falls back to distance+score sort if untrained."""
        if self._model is None:
            return self._fallback_rank(products, n)

        X = np.array([_feature_vector(p) for p in products])
        try:
            X_scaled = self._scaler.transform(X)
            scores = self._model.predict_proba(X_scaled)[:, 1]
        except Exception:
            return self._fallback_rank(products, n)

        ranked = sorted(zip(scores, products), key=lambda x: -x[0])
        return [p for _, p in ranked[:n]]

    @staticmethod
    def _fallback_rank(products: list[dict], n: int) -> list[dict]:
        def score(p):
            return (
                min(p.get("km", 9999) / 100, 10)
                + SCORE_MAP.get(p.get("ns"), 3)
                + SCORE_MAP.get(p.get("es"), 3)
            )

        return sorted(products, key=score)[:n]
