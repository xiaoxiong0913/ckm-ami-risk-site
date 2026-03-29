# CKM-AMI Risk Site

Public-facing CKM-AMI risk calculator and reporting atlas bundle.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/xiaoxiong0913/ckm-ami-risk-site)

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
