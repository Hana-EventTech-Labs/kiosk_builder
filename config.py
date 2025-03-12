import json

with open("resources/config.json", "r") as f:
    config = json.load(f)

screen_order = config.get("screen_order", [0, 1, 2, 3, 4, 5])