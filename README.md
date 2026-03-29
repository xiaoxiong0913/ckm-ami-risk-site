# CKM-AMI Risk Site

Public-facing CKM-AMI risk calculator and reporting atlas bundle.

## Runtime

- Framework: Flask
- Public APIs:
  - `GET /api/config`
  - `GET /health`
  - `POST /api/predict`
- Locked runtime model: `Champion model: XGBoost`

## Local Run

```bash
pip install -r requirements.txt
python app.py
```

## Render

This repository is prepared for a Render Python Web Service using the root-level `render.yaml`, `Procfile`, and `requirements.txt`.
