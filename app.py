from __future__ import annotations

import json
import pickle
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
with (BASE_DIR / "site payload.json").open("r", encoding="utf-8") as file:
    SITE_CONFIG = json.load(file)
with (BASE_DIR / "runtime" / "mimic_locked_model.pkl").open("rb") as file:
    MODEL_PACKAGE = pickle.load(file)
FEATURE_NAMES = list(MODEL_PACKAGE["feature_names"])
INPUT_SCHEMA = {item["key"]: item for item in SITE_CONFIG["calculator"]["inputs"]}

app = Flask(__name__)

def _coerce_value(key: str, value):
    schema = INPUT_SCHEMA[key]
    if schema["type"] == "choice":
        mapping = schema.get("mapping", {})
        if value not in mapping:
            raise ValueError("invalid_choice")
        return mapping[value]
    if schema["type"] == "binary":
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)) and value in {0, 1}:
            return int(value)
        if isinstance(value, str) and value.strip() in {"0", "1"}:
            return int(value.strip())
        raise ValueError("invalid_binary")
    try:
        numeric = float(value)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("invalid_number") from exc
    if schema.get("min") is not None and numeric < float(schema["min"]):
        raise ValueError("below_min")
    if schema.get("max") is not None and numeric > float(schema["max"]):
        raise ValueError("above_max")
    return numeric

def _prepare_frame(inputs: dict[str, object]) -> pd.DataFrame:
    missing = [key for key in FEATURE_NAMES if key not in inputs]
    if missing:
        raise ValueError(json.dumps({"missing": missing}))
    row = {}
    errors = {}
    for key in FEATURE_NAMES:
        try:
            row[key] = _coerce_value(key, inputs[key])
        except ValueError as exc:
            errors[key] = str(exc)
    if errors:
        raise ValueError(json.dumps(errors))
    return pd.DataFrame([row], columns=FEATURE_NAMES)

def _classify(probability: float):
    low = float(SITE_CONFIG["calculator"]["thresholds"]["low"])
    high = float(SITE_CONFIG["calculator"]["thresholds"]["high"])
    if probability < low:
        return "Low", f"Below the public-site lower monitoring threshold (< {low:.2f})."
    if probability < high:
        return "Intermediate", f"Between the public-site lower and upper thresholds ({low:.2f} to < {high:.2f})."
    return "High", f"At or above the public-site upper monitoring threshold (>= {high:.2f})."

@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.get("/assets/<path:filename>")
def assets(filename: str):
    return send_from_directory(BASE_DIR / "assets", filename)

@app.get("/downloads/<path:filename>")
def downloads(filename: str):
    return send_from_directory(BASE_DIR / "downloads", filename)

@app.get("/api/config")
def api_config():
    return jsonify(SITE_CONFIG)

@app.post("/api/predict")
def api_predict():
    payload = request.get_json(silent=True) or {}
    inputs = payload.get("inputs")
    if not isinstance(inputs, dict):
        return jsonify({"error": "invalid_input", "details": {"inputs": "expected_object"}}), 400
    try:
        frame = _prepare_frame(inputs)
    except ValueError as exc:
        try:
            details = json.loads(str(exc))
        except Exception:  # noqa: BLE001
            details = {"inputs": str(exc)}
        return jsonify({"error": "invalid_input", "details": details}), 400
    transformed = pd.DataFrame(MODEL_PACKAGE["imputer"].transform(frame), columns=FEATURE_NAMES)
    probability = float(MODEL_PACKAGE["model"].predict_proba(transformed)[:, 1][0])
    risk_tier, interpretation = _classify(probability)
    return jsonify({"model_name": SITE_CONFIG["calculator"]["model_name"], "version_note": SITE_CONFIG["calculator"]["version_note"], "predicted_probability": probability, "risk_tier": risk_tier, "threshold_interpretation": interpretation, "caution_note": SITE_CONFIG["calculator"]["caution_note"]})

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
