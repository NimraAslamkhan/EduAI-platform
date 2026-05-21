"""
ML Pipeline - Student performance prediction and dropout risk detection.
Uses scikit-learn (RandomForest + GradientBoosting) with auto model selection.
"""

import os
import logging
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
from sklearn.impute import SimpleImputer

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "../../../models")
os.makedirs(MODEL_DIR, exist_ok=True)


class StudentMLPipeline:
    """
    Modular ML pipeline for:
    - Performance prediction (pass/fail)
    - Dropout risk classification (low/medium/high)
    - Attendance risk flagging
    """

    def __init__(self):
        self.performance_model = None
        self.dropout_model = None
        self.scaler = StandardScaler()
        self.label_encoder_gender = LabelEncoder()
        self.label_encoder_class = LabelEncoder()
        self.is_trained = False

        # Try loading pre-trained models
        self._load_models()

    def _get_model_path(self, name: str) -> str:
        return os.path.join(MODEL_DIR, f"{name}.pkl")

    def _save_models(self):
        """Persist trained models to disk."""
        try:
            joblib.dump(self.performance_model, self._get_model_path("performance"))
            joblib.dump(self.dropout_model, self._get_model_path("dropout"))
            joblib.dump(self.scaler, self._get_model_path("scaler"))
            joblib.dump(self.label_encoder_gender, self._get_model_path("le_gender"))
            joblib.dump(self.label_encoder_class, self._get_model_path("le_class"))
            logger.info("ML models saved to disk")
        except Exception as e:
            logger.warning(f"Could not save models: {e}")

    def _load_models(self):
        """Load pre-trained models from disk."""
        try:
            if all(os.path.exists(self._get_model_path(n))
                   for n in ["performance", "dropout", "scaler", "le_gender", "le_class"]):
                self.performance_model = joblib.load(self._get_model_path("performance"))
                self.dropout_model = joblib.load(self._get_model_path("dropout"))
                self.scaler = joblib.load(self._get_model_path("scaler"))
                self.label_encoder_gender = joblib.load(self._get_model_path("le_gender"))
                self.label_encoder_class = joblib.load(self._get_model_path("le_class"))
                self.is_trained = True
                logger.info("Loaded pre-trained ML models from disk")
        except Exception as e:
            logger.warning(f"Could not load saved models: {e}")

    def _preprocess_features(self, data: list, fit: bool = False) -> np.ndarray:
        """
        Convert raw student data to feature matrix.
        Features: age, study_hours, attendance_rate, avg_score (only for dropout),
                  gender_encoded, class_encoded
        """
        df = pd.DataFrame(data)

        # Fill missing values
        df["age"] = pd.to_numeric(df.get("age", 14), errors="coerce").fillna(14)
        df["study_hours"] = pd.to_numeric(df.get("study_hours", 3), errors="coerce").fillna(3)
        df["attendance_rate"] = pd.to_numeric(df.get("attendance_rate", 75), errors="coerce").fillna(75)
        df["avg_score"] = pd.to_numeric(df.get("avg_score", 60), errors="coerce").fillna(60)

        # Encode categorical
        gender_vals = df["gender"].fillna("Unknown").astype(str).values
        class_vals = df["class_name"].fillna("Unknown").astype(str).values

        if fit:
            gender_enc = self.label_encoder_gender.fit_transform(gender_vals)
            class_enc = self.label_encoder_class.fit_transform(class_vals)
        else:
            # Handle unseen labels gracefully
            try:
                gender_enc = self.label_encoder_gender.transform(gender_vals)
            except ValueError:
                gender_enc = np.zeros(len(gender_vals))
            try:
                class_enc = self.label_encoder_class.transform(class_vals)
            except ValueError:
                class_enc = np.zeros(len(class_vals))

        features = np.column_stack([
            df["age"].values,
            df["study_hours"].values,
            df["attendance_rate"].values,
            df["avg_score"].values,
            gender_enc,
            class_enc,
        ])

        return features

    def _generate_performance_labels(self, data: list) -> np.ndarray:
        """Label: 1 = pass (avg_score >= 50), 0 = fail."""
        return np.array([1 if d.get("avg_score", 0) >= 50 else 0 for d in data])

    def _generate_dropout_labels(self, data: list) -> np.ndarray:
        """
        Label: 0=low_risk, 1=medium_risk, 2=high_risk
        Based on attendance + avg_score heuristic.
        """
        labels = []
        for d in data:
            score = d.get("avg_score", 60) or 60
            att = d.get("attendance_rate", 80) or 80
            risk = 0
            if score < 40:
                risk += 2
            elif score < 55:
                risk += 1
            if att < 60:
                risk += 2
            elif att < 75:
                risk += 1
            labels.append(min(2, risk))
        return np.array(labels)

    def _select_best_model(self, X_train, y_train, X_val, y_val, candidates: dict) -> object:
        """Train all candidate models and return the best one."""
        best_model = None
        best_score = -1

        for name, model in candidates.items():
            try:
                model.fit(X_train, y_train)
                score = accuracy_score(y_val, model.predict(X_val))
                logger.info(f"  {name}: val accuracy = {score:.3f}")
                if score > best_score:
                    best_score = score
                    best_model = model
            except Exception as e:
                logger.warning(f"  {name} failed: {e}")

        logger.info(f"Best model accuracy: {best_score:.3f}")
        return best_model

    def train(self, data: list) -> dict:
        """
        Train both pipelines on the provided student data.
        Returns a dict of training metrics.
        """
        if len(data) < 10:
            logger.warning("Not enough data for ML training (need >= 10 records)")
            return {"error": "Insufficient data"}

        try:
            logger.info(f"Training ML models on {len(data)} student records...")

            X = self._preprocess_features(data, fit=True)
            y_perf = self._generate_performance_labels(data)
            y_drop = self._generate_dropout_labels(data)

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Split
            X_tr, X_val, yp_tr, yp_val = train_test_split(
                X_scaled, y_perf, test_size=0.2, random_state=42
            )
            _, _, yd_tr, yd_val = train_test_split(
                X_scaled, y_drop, test_size=0.2, random_state=42
            )

            # Candidate models
            perf_candidates = {
                "RandomForest": RandomForestClassifier(n_estimators=100, max_depth=6,
                                                        random_state=42, n_jobs=-1),
                "GradientBoosting": GradientBoostingClassifier(n_estimators=100,
                                                                max_depth=4, random_state=42),
                "LogisticRegression": LogisticRegression(max_iter=500, random_state=42),
            }
            drop_candidates = {
                "RandomForest": RandomForestClassifier(n_estimators=100, max_depth=6,
                                                        random_state=42, n_jobs=-1),
                "GradientBoosting": GradientBoostingClassifier(n_estimators=100,
                                                                max_depth=4, random_state=42),
            }

            logger.info("Training performance model...")
            self.performance_model = self._select_best_model(X_tr, yp_tr, X_val, yp_val, perf_candidates)

            logger.info("Training dropout risk model...")
            self.dropout_model = self._select_best_model(
                X_scaled, yd_tr[:len(X_scaled)], X_val, yd_val, drop_candidates
            )

            # Final metrics
            perf_acc = accuracy_score(yp_val, self.performance_model.predict(X_val))
            drop_acc = accuracy_score(yd_val, self.dropout_model.predict(X_val))

            self.is_trained = True
            self._save_models()

            metrics = {
                "performance_accuracy": round(perf_acc * 100, 1),
                "dropout_accuracy": round(drop_acc * 100, 1),
                "total_records": len(data),
                "pass_rate": round(sum(y_perf) / len(y_perf) * 100, 1),
                "high_risk_count": int(sum(y_drop >= 2)),
            }
            logger.info(f"Training complete: {metrics}")
            return metrics

        except Exception as e:
            logger.error(f"ML training error: {e}", exc_info=True)
            return {"error": str(e)}

    def predict_performance(self, student_data: dict) -> dict:
        """
        Predict if a student will pass or fail.
        Returns: {'prediction': 'Pass'/'Fail', 'probability': float, 'confidence': str}
        """
        if not self.is_trained:
            return self._rule_based_performance(student_data)

        try:
            X = self._preprocess_features([student_data], fit=False)
            X_scaled = self.scaler.transform(X)
            pred = self.performance_model.predict(X_scaled)[0]
            proba = self.performance_model.predict_proba(X_scaled)[0]
            confidence_val = max(proba) * 100

            return {
                "prediction": "Pass" if pred == 1 else "Fail",
                "probability": round(confidence_val, 1),
                "confidence": "High" if confidence_val > 80 else "Medium" if confidence_val > 60 else "Low",
                "pass_probability": round(proba[1] * 100 if len(proba) > 1 else confidence_val, 1),
            }
        except Exception as e:
            logger.error(f"Performance prediction error: {e}")
            return self._rule_based_performance(student_data)

    def predict_dropout_risk(self, student_data: dict) -> dict:
        """
        Predict dropout risk level for a student.
        Returns: {'risk_level': str, 'risk_score': float, 'factors': list}
        """
        if not self.is_trained:
            return self._rule_based_dropout(student_data)

        try:
            X = self._preprocess_features([student_data], fit=False)
            X_scaled = self.scaler.transform(X)
            pred = self.dropout_model.predict(X_scaled)[0]
            proba = self.dropout_model.predict_proba(X_scaled)[0]

            level_map = {0: "Low", 1: "Medium", 2: "High"}
            risk_score = round((pred / 2) * 100, 1)

            factors = []
            if student_data.get("avg_score", 100) < 50:
                factors.append("Low academic performance")
            if student_data.get("attendance_rate", 100) < 75:
                factors.append("Poor attendance")
            if student_data.get("study_hours", 5) < 2:
                factors.append("Insufficient study hours")

            return {
                "risk_level": level_map[pred],
                "risk_score": risk_score,
                "factors": factors,
                "probabilities": {level_map[i]: round(p * 100, 1) for i, p in enumerate(proba)},
            }
        except Exception as e:
            logger.error(f"Dropout prediction error: {e}")
            return self._rule_based_dropout(student_data)

    def predict_bulk(self, data: list) -> list:
        """Run predictions for all students. Returns augmented list."""
        results = []
        for student in data:
            perf = self.predict_performance(student)
            drop = self.predict_dropout_risk(student)
            results.append({
                **student,
                "predicted_outcome": perf.get("prediction", "N/A"),
                "pass_probability": perf.get("pass_probability", 0),
                "dropout_risk": drop.get("risk_level", "N/A"),
                "risk_score": drop.get("risk_score", 0),
            })
        return results

    def generate_ai_alerts(self, data: list, db=None, school_id: int = 1, persist: bool = True) -> dict:
        """
        Generate AI alerts and recommendations from student data.
        - data: list of student dicts (as returned by get_performance_data_for_ml)
        - db: optional DatabaseManager instance to persist alerts
        - school_id: school identifier
        - persist: when True and db provided, save alerts to ai_alerts table

        Returns summary dict with counts and list of alerts.
        """
        try:
            preds = self.predict_bulk(data)
            alerts = []
            for p in preds:
                sid = p.get("student_id")
                cls = p.get("class_name")
                name = p.get("full_name") or p.get("student_name") or f"Student {sid}"

                # High-priority dropout risk
                if p.get("dropout_risk") == "High" or p.get("risk_score", 0) >= 70:
                    title = f"Dropout Risk: {name}"
                    message = f"Risk score {p.get('risk_score')} — immediate counseling and parent contact recommended."
                    severity = "critical" if p.get("dropout_risk") == "High" else "high"
                    alerts.append({"student_id": sid, "class": cls, "title": title, "message": message, "severity": severity, "type": "dropout_risk"})

                # Attendance drop / low attendance
                if p.get("attendance_rate", 100) < 65:
                    title = f"{name} attendance dropped"
                    message = f"Attendance at {p.get('attendance_rate')}% — consider parent contact and attendance plan."
                    alerts.append({"student_id": sid, "class": cls, "title": title, "message": message, "severity": "high", "type": "attendance_drop"})

                # Low performance
                if p.get("pass_probability", 100) < 50 or p.get("avg_score", 100) < 45:
                    title = f"Performance Alert: {name}"
                    message = f"Pass probability {p.get('pass_probability')}% — academic intervention recommended."
                    alerts.append({"student_id": sid, "class": cls, "title": title, "message": message, "severity": "high", "type": "low_performance"})

            # Persist alerts
            persisted = 0
            if persist and db is not None:
                for a in alerts:
                    try:
                        db.add_ai_alert(school_id=school_id, student_id=a.get('student_id'), class_id=None,
                                        alert_type=a.get('type'), severity=a.get('severity'), title=a.get('title'), message=a.get('message'))
                        persisted += 1
                    except Exception:
                        continue

            return {"total_alerts": len(alerts), "persisted": persisted, "alerts": alerts}
        except Exception as e:
            logger.error(f"Error generating AI alerts: {e}")
            return {"error": str(e)}

    def get_feature_importance(self) -> dict:
        """Return feature importances from the best model."""
        feature_names = ["Age", "Study Hours", "Attendance Rate", "Avg Score",
                         "Gender", "Class Level"]
        if not self.is_trained:
            return {}
        try:
            imp = self.performance_model.feature_importances_
            return dict(zip(feature_names, [round(v * 100, 1) for v in imp]))
        except Exception:
            return {}

    # Rule-based fallbacks when ML model is not trained
    def _rule_based_performance(self, d: dict) -> dict:
        score = d.get("avg_score") or 0
        att = d.get("attendance_rate") or 0
        pass_prob = min(100, max(0, score * 0.7 + att * 0.3))
        return {
            "prediction": "Pass" if score >= 50 else "Fail",
            "probability": round(pass_prob, 1),
            "confidence": "Medium",
            "pass_probability": round(pass_prob, 1),
        }

    def _rule_based_dropout(self, d: dict) -> dict:
        score = d.get("avg_score") or 60
        att = d.get("attendance_rate") or 80
        risk = 0
        factors = []
        if score < 40:
            risk += 40
            factors.append("Very low academic performance")
        elif score < 55:
            risk += 20
            factors.append("Below average performance")
        if att < 60:
            risk += 40
            factors.append("Critical attendance issue")
        elif att < 75:
            risk += 20
            factors.append("Low attendance")
        if d.get("study_hours", 5) < 2:
            risk += 10
            factors.append("Low study hours")

        level = "High" if risk >= 50 else "Medium" if risk >= 25 else "Low"
        return {"risk_level": level, "risk_score": min(100, risk), "factors": factors}
