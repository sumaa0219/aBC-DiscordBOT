import scr.database as db
import os
import json
from decimal import Decimal


# 設定ファイルの読み込み
with open(f"setting.json", "r", encoding="UTF-8") as f:
    settings = json.load(f)

for key in settings.keys():
    db.writeDB("settings", key, settings[key])
# import json
# from decimal import Decimal


# def getSettings():
#     data = db.readDB("settings")

#     def convert_large_numbers(obj):
#         if isinstance(obj, (int, float)) and (obj > 1e18 or obj < -1e18):
#             return str(Decimal(obj))
#         return obj

#     with open("setting.json", "w", encoding="UTF-8") as f:
#         json.dump(data, f, indent=4, ensure_ascii=False,
#                   default=convert_large_numbers)

#     print("setting.json updated")


# getSettings()
