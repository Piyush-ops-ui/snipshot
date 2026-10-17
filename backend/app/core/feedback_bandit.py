"""
Weapon 6: PedagogyScore Contextual Bandit.
Maintains an SQLite database (data/db/snipshot.db) storing feature vectors and viewer engagement telemetry.
Performs online LinUCB / Bayesian weight updates (w1..w5) so highlight scoring continuously improves
based on retention and user export signals.
"""

from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path
import sqlite3
import json
from datetime import datetime, timezone
import numpy as np

from backend.app.config import settings


class PedagogyScoreBandit:
    """
    Weapon 6: SQLite-backed Contextual Bandit for Pedagogical Highlight Scoring.
    Tracks feature vectors [x1..x5] and updates weights [w1..w5] via online ridge/LinUCB learning
    from viewer retention and export signals.
    """

    FEATURE_KEYS = ["rms_audio", "diff_visual", "tech_density", "bug2fix_bonus", "penalty_deictic"]
    WEIGHT_KEYS = ["w1", "w2", "w3", "w4", "w5"]

    # Domain Priors
    DEFAULT_WEIGHTS = {
        "w1": 0.15,   # Audio RMS prosody
        "w2": 0.25,   # Visual typing diff density
        "w3": 0.25,   # Technical term density
        "w4": 0.35,   # Bug-to-fix triad bonus
        "w5": 2.00,   # Deictic entry penalty
    }

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        alpha: float = 0.2,
        l2_reg: float = 1.0,
        model_name: str = "pedagogy_highlight_bandit",
    ):
        self.db_path = str(db_path or settings.DB_PATH)
        self.alpha = alpha
        self.l2_reg = l2_reg
        self.model_name = model_name

        # Ensure directory exists if not an in-memory db
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # If in-memory, hold a single connection
        self._mem_conn = sqlite3.connect(":memory:") if self.db_path == ":memory:" else None
        if self._mem_conn:
            self._mem_conn.row_factory = sqlite3.Row

        self._init_db()
        self._load_or_init_weights()

    def _get_connection(self) -> sqlite3.Connection:
        if self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes tables for bandit state and telemetry history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bandit_weights (
                    id INTEGER PRIMARY KEY,
                    model_name TEXT UNIQUE,
                    w1 REAL NOT NULL,
                    w2 REAL NOT NULL,
                    w3 REAL NOT NULL,
                    w4 REAL NOT NULL,
                    w5 REAL NOT NULL,
                    covariance_matrix TEXT NOT NULL,
                    bias_vector TEXT NOT NULL,
                    sample_count INTEGER NOT NULL,
                    last_updated TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS viewer_telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reel_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    features_json TEXT NOT NULL,
                    weights_json TEXT NOT NULL,
                    retention_rate REAL NOT NULL,
                    exported INTEGER NOT NULL,
                    reward REAL NOT NULL
                )
            """)
            conn.commit()

    def _load_or_init_weights(self):
        """Loads weights and covariance matrix from SQLite or registers initial priors."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM bandit_weights WHERE model_name = ?", (self.model_name,)
            )
            row = cursor.fetchone()

            if row:
                self.w1 = float(row["w1"])
                self.w2 = float(row["w2"])
                self.w3 = float(row["w3"])
                self.w4 = float(row["w4"])
                self.w5 = float(row["w5"])
                self.A = np.array(json.loads(row["covariance_matrix"]), dtype=np.float64)
                self.b = np.array(json.loads(row["bias_vector"]), dtype=np.float64)
                self.sample_count = int(row["sample_count"])
            else:
                # Initialize with prior weights and L2 identity
                self.w1 = self.DEFAULT_WEIGHTS["w1"]
                self.w2 = self.DEFAULT_WEIGHTS["w2"]
                self.w3 = self.DEFAULT_WEIGHTS["w3"]
                self.w4 = self.DEFAULT_WEIGHTS["w4"]
                self.w5 = self.DEFAULT_WEIGHTS["w5"]

                d = len(self.FEATURE_KEYS)
                self.A = self.l2_reg * np.eye(d, dtype=np.float64)
                prior_vec = np.array([self.w1, self.w2, self.w3, self.w4, -self.w5], dtype=np.float64)
                self.b = self.A @ prior_vec
                self.sample_count = 0

                cursor.execute("""
                    INSERT INTO bandit_weights (
                        model_name, w1, w2, w3, w4, w5, covariance_matrix, bias_vector, sample_count, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.model_name,
                    self.w1,
                    self.w2,
                    self.w3,
                    self.w4,
                    self.w5,
                    json.dumps(self.A.tolist()),
                    json.dumps(self.b.tolist()),
                    self.sample_count,
                    datetime.now(timezone.utc).isoformat(),
                ))
                conn.commit()

    def get_weights(self) -> Dict[str, float]:
        """Returns the current highlight scoring weights."""
        return {
            "w1": round(self.w1, 4),
            "w2": round(self.w2, 4),
            "w3": round(self.w3, 4),
            "w4": round(self.w4, 4),
            "w5": round(self.w5, 4),
            "w_prosody": round(self.w1, 4),
            "w_visual": round(self.w2, 4),
            "w_tech": round(self.w3, 4),
            "w_triad": round(self.w4, 4),
            "w_deictic": round(self.w5, 4),
        }

    def _extract_feature_vector(self, features: Union[Dict[str, float], List[float], np.ndarray]) -> np.ndarray:
        if isinstance(features, (list, tuple, np.ndarray)):
            if len(features) != 5:
                raise ValueError(f"Feature vector must have 5 elements, got {len(features)}")
            return np.array(features, dtype=np.float64)

        if isinstance(features, dict):
            # Map standard keys
            rms = features.get("rms_audio", features.get("w1", 0.0))
            diff = features.get("diff_visual", features.get("w2", 0.0))
            tech = features.get("tech_density", features.get("w3", 0.0))
            triad = features.get("bug2fix_bonus", features.get("w4", 0.0))
            deictic = features.get("penalty_deictic", features.get("w5", 0.0))
            return np.array([rms, diff, tech, triad, deictic], dtype=np.float64)

        raise TypeError(f"Unsupported features type: {type(features)}")

    def predict_score(
        self,
        features: Union[Dict[str, float], List[float], np.ndarray],
        use_exploration: bool = False,
    ) -> float:
        """
        Calculates predicted pedagogical triad score:
        S = w1 * RMS + w2 * Diff + w3 * Tech + w4 * Triad - w5 * Penalty
        Optionally adds LinUCB exploration bonus alpha * sqrt(x^T A^{-1} x).
        """
        x = self._extract_feature_vector(features)
        # S_triad = w1*x1 + w2*x2 + w3*x3 + w4*x4 - w5*x5
        score = (
            (self.w1 * x[0])
            + (self.w2 * x[1])
            + (self.w3 * x[2])
            + (self.w4 * x[3])
            - (self.w5 * x[4])
        )

        if use_exploration:
            try:
                A_inv = np.linalg.inv(self.A)
                ucb_bonus = self.alpha * float(np.sqrt(np.dot(x, np.dot(A_inv, x))))
                score += ucb_bonus
            except Exception:
                pass

        return round(float(score), 4)

    def record_feedback(
        self,
        reel_id: str,
        features: Union[Dict[str, float], List[float], np.ndarray],
        retention_rate: float,
        exported: bool,
    ) -> Dict[str, float]:
        """
        Online Bayesian / Ridge weight update:
        Ingests user export signal and retention rate (0.0 to 1.0).
        Calculates composite reward r, updates covariance matrix A and bias vector b,
        and solves for updated weights w1..w5.
        """
        x = self._extract_feature_vector(features)
        retention_clamped = max(0.0, min(1.0, float(retention_rate)))
        export_val = 1.0 if exported else 0.0

        # Composite reward: 50% viewer retention, 50% explicit user export
        reward = (0.5 * retention_clamped) + (0.5 * export_val)

        # Context vector for linear model: notice deictic is negative impact
        x_ctx = np.array([x[0], x[1], x[2], x[3], -x[4]], dtype=np.float64)

        # Online ridge update: A = A + x x^T, b = b + r * x
        self.A += np.outer(x_ctx, x_ctx)
        self.b += reward * x_ctx
        self.sample_count += 1

        # Solve for updated parameters theta
        try:
            theta = np.linalg.solve(self.A, self.b)
        except np.linalg.LinAlgError:
            theta = np.linalg.pinv(self.A) @ self.b

        # Bayesian blending with prior weights to ensure stability under low sample counts
        prior_weight = 5.0 / (5.0 + self.sample_count)
        prior_vec = np.array([
            self.DEFAULT_WEIGHTS["w1"],
            self.DEFAULT_WEIGHTS["w2"],
            self.DEFAULT_WEIGHTS["w3"],
            self.DEFAULT_WEIGHTS["w4"],
            -self.DEFAULT_WEIGHTS["w5"],
        ], dtype=np.float64)

        blended = (prior_weight * prior_vec) + ((1.0 - prior_weight) * theta)

        # Clamping to sensible bounded intervals
        self.w1 = round(float(np.clip(blended[0], 0.05, 1.50)), 4)
        self.w2 = round(float(np.clip(blended[1], 0.05, 1.50)), 4)
        self.w3 = round(float(np.clip(blended[2], 0.05, 1.50)), 4)
        self.w4 = round(float(np.clip(blended[3], 0.05, 2.00)), 4)
        self.w5 = round(float(np.clip(-blended[4], 0.50, 5.00)), 4)

        # Save updated state to SQLite
        now_iso = datetime.now(timezone.utc).isoformat()
        current_weights = self.get_weights()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE bandit_weights
                SET w1 = ?, w2 = ?, w3 = ?, w4 = ?, w5 = ?,
                    covariance_matrix = ?, bias_vector = ?, sample_count = ?, last_updated = ?
                WHERE model_name = ?
            """, (
                self.w1,
                self.w2,
                self.w3,
                self.w4,
                self.w5,
                json.dumps(self.A.tolist()),
                json.dumps(self.b.tolist()),
                self.sample_count,
                now_iso,
                self.model_name,
            ))

            cursor.execute("""
                INSERT INTO viewer_telemetry (
                    reel_id, timestamp, features_json, weights_json, retention_rate, exported, reward
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                reel_id,
                now_iso,
                json.dumps(x.tolist()),
                json.dumps(current_weights),
                retention_clamped,
                1 if exported else 0,
                reward,
            ))
            conn.commit()

        return current_weights

    def get_telemetry_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetches the latest viewer telemetry and bandit reward logs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM viewer_telemetry ORDER BY id DESC LIMIT ?", (limit,)
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": r["id"],
                    "reel_id": r["reel_id"],
                    "timestamp": r["timestamp"],
                    "features": json.loads(r["features_json"]),
                    "weights": json.loads(r["weights_json"]),
                    "retention_rate": r["retention_rate"],
                    "exported": bool(r["exported"]),
                    "reward": r["reward"],
                }
                for r in rows
            ]

    def reset(self, preserve_history: bool = True):
        """Resets bandit weights and covariance matrix to default priors."""
        self.w1 = self.DEFAULT_WEIGHTS["w1"]
        self.w2 = self.DEFAULT_WEIGHTS["w2"]
        self.w3 = self.DEFAULT_WEIGHTS["w3"]
        self.w4 = self.DEFAULT_WEIGHTS["w4"]
        self.w5 = self.DEFAULT_WEIGHTS["w5"]

        d = len(self.FEATURE_KEYS)
        self.A = self.l2_reg * np.eye(d, dtype=np.float64)
        prior_vec = np.array([self.w1, self.w2, self.w3, self.w4, -self.w5], dtype=np.float64)
        self.b = self.A @ prior_vec
        self.sample_count = 0

        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE bandit_weights
                SET w1 = ?, w2 = ?, w3 = ?, w4 = ?, w5 = ?,
                    covariance_matrix = ?, bias_vector = ?, sample_count = ?, last_updated = ?
                WHERE model_name = ?
            """, (
                self.w1,
                self.w2,
                self.w3,
                self.w4,
                self.w5,
                json.dumps(self.A.tolist()),
                json.dumps(self.b.tolist()),
                self.sample_count,
                now_iso,
                self.model_name,
            ))
            if not preserve_history:
                cursor.execute("DELETE FROM viewer_telemetry")
            conn.commit()
