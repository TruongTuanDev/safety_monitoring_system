# safety_monitoring_system
Đồ án chuyên ngành 2

## Authentication (MongoDB)

This project now supports a simple console-based login/register flow backed by MongoDB.

Configuration:

- Edit `config.yaml` -> `database.mongo_uri` and `database.mongo_db` to point to your MongoDB instance.

Install dependencies (example):

```powershell
pip install -r requirements.txt
```

Usage:

- When you run the app (`python main.py`) you'll be prompted to Login or Register before the camera starts.

