import requests
import json

header = {
    "Content-Type": "application/json; charset=utf-8",
    "Authorization": "Basic ZmExNDg0ZTQtNmEyNi00M2QxLWFjYjYtZDliNjQyYjU5MzYz",
}

payload = {
    "app_id": "6cc33c87-b167-4863-a6b9-2ed884872e79",
    "contents": {"en": "test"},
    "include_player_ids": ["e4066201-d77b-43ca-9df7-08064d3b398b"],
}

req = requests.post(
    "https://onesignal.com/api/v1/notifications",
    headers=header,
    data=json.dumps(payload),
)

print (req.text)