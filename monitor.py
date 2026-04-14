import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime
import pickle
import os

class ContractMonitor:
    def __init__(self, app_id: str):
        self.app_id = app_id
        self.model = IsolationForest(
            contamination=0.05,  # assume 5% of transactions are anomalous
            random_state=42,
            n_estimators=100
        )
        self.transaction_history = []
        self.is_trained = False
        # Create models directory if it doesn't exist
        os.makedirs("models", exist_ok=True)
        self.model_path = f"models/monitor_{app_id}.pkl"
        
        # Try to load existing model
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
                self.is_trained = True
    
    def extract_features(self, transaction: dict) -> list:
        """
        Extract numerical features from a raw Algorand transaction dict.
        """
        features = [
            transaction.get("payment-transaction", {}).get("amount", 0),  # ALGO amount in microalgos
            transaction.get("fee", 0),                                   # Transaction fee
            len(transaction.get("note", b"") or b""),                   # Note field length
            1 if transaction.get("rekey-to") else 0,                    # Rekey flag
            1 if transaction.get("close-remainder-to") else 0,          # Close flag
            len(transaction.get("inner-txns", [])) if transaction.get("inner-txns") else 0,  # Inner txn count
        ]
        return features
    
    def add_transactions(self, transactions: list):
        """Feed new transactions into the monitor and retrain if needed."""
        for txn in transactions:
            features = self.extract_features(txn)
            self.transaction_history.append(features)
        
        # Retrain model if we have enough data (threshold: 10)
        if len(self.transaction_history) >= 10:
            self._train()
    
    def _train(self):
        """Train the Isolation Forest and save the model."""
        X = np.array(self.transaction_history)
        self.model.fit(X)
        self.is_trained = True
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
    
    def check_transaction(self, transaction: dict) -> dict:
        """
        Check if a new transaction is anomalous.
        """
        if not self.is_trained:
            return {
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "description": "Not enough historical data yet (need 10+ transactions)",
                "severity": "info"
            }
        
        features = np.array([self.extract_features(transaction)])
        
        # Isolation Forest: -1 = anomaly, 1 = normal
        prediction = self.model.predict(features)[0]
        raw_score = self.model.score_samples(features)[0]
        
        # Convert to 0-1 scale (more positive = more anomalous)
        anomaly_score = max(0, min(1, (-raw_score - 0.3) * 2))
        
        is_anomaly = prediction == -1
        
        # Generate human-readable description
        description = self._describe_anomaly(transaction, is_anomaly, anomaly_score)
        severity = self._get_severity(anomaly_score) if is_anomaly else "normal"
        
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(anomaly_score, 3),
            "description": description,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        }

    def _describe_anomaly(self, transaction: dict, is_anomaly: bool, score: float) -> str:
        """Generate a human-readable alert message."""
        if not is_anomaly:
            return "Transaction is within normal patterns."
        
        flags = []
        
        amount = transaction.get("payment-transaction", {}).get("amount", 0)
        if amount > 1_000_000_000:  # > 1000 ALGO
            flags.append(f"Unusually large transfer: {amount / 1_000_000:.2f} ALGO")
        
        if transaction.get("rekey-to"):
            flags.append("⚠️ REKEY operation detected — account authorization change")
        
        if transaction.get("close-remainder-to"):
            flags.append("⚠️ CLOSE_REMAINDER_TO set — account draining attempt possible")
        
        inner_txns = transaction.get("inner-txns", [])
        if len(inner_txns) > 5:
            flags.append(f"High inner transaction count: {len(inner_txns)}")
        
        if flags:
            return " | ".join(flags)
        
        return f"Statistical anomaly detected (score: {score:.2f}). Unusual transaction pattern."

    def _get_severity(self, score: float) -> str:
        if score > 0.8: return "Critical"
        if score > 0.6: return "High"
        if score > 0.4: return "Medium"
        return "Low"

# Global registry of monitors
_monitors = {}

def get_monitor(app_id: str) -> ContractMonitor:
    if app_id not in _monitors:
        _monitors[app_id] = ContractMonitor(app_id)
    return _monitors[app_id]
