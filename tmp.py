import requests
import json

header = {
    "Content-Type": "application/json; charset=utf-8",
    "Authorization": "Basic ZWI5ODBiZDctNWIyMS00ZDM3LTk1MTctMDk2YjVhYTU5MWJk",
}

payload = {
    "app_id": "6cc33c87-b167-4863-a6b9-2ed884872e79",
    "contents": {"en": "شما بازی جان جیبی رو نصب کرید. اگر تا الآن وارد بازی نشدید، نام کاربری دلخواهتون رو انتخاب کنید و با کد دعوت can1100 وارد بازی بشید و جایزه بگیرید."},
    "include_player_ids": ['6ec5e683-392e-48df-9473-10d31a0401c6', '29838506-ae35-46c0-a54e-8830325934e7', '0b3b7d52-d23c-4cd9-9fd4-5db3ddc8bba5', '92eedd35-f444-4a94-b724-ce654c61a9a9', 'e25d418d-ad54-40dc-9e48-a6b11b88d894', 'e4066201-d77b-43ca-9df7-08064d3b398b', 'e83804e7-3991-45e0-84d2-e605921cec14'],
}

req = requests.post(
    "https://onesignal.com/api/v1/notifications",
    headers=header,
    data=json.dumps(payload),
)

print (req.text)