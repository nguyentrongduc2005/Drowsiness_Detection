import json
import os

def load_config():
    config_path = os.path.join("data", "config.json")
    with open(config_path, "r") as f:
        return json.load(f)

# Cách sử dụng trong main.py hoặc detector.py
# settings = load_config()
# ear_limit = settings['eye_thresholds']['ear_limit']