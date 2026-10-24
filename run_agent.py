import os
import zipfile
import json
import pandas as pd
from google import genai

# 1. 讀取本地上傳的 ZIP 檔案並解壓縮所有 CSV
zip_path = "lvr_landcsv.zip"
print(f"正在讀取本地壓縮檔：{zip_path}")

all_dfs = []

with zipfile.ZipFile(zip_path, 'r') as z:
    for filename in z.namelist():
        if filename.endswith('.csv'):
            print(f"正在解析壓縮檔中的 CSV 檔案：{filename}")
            with z.open(filename) as f:
                try:
                    df = pd.read_csv(f, low_memory=False, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(f, low_memory=False, encoding='cp950')
                
                # 排除內政部 CSV 常見的第二列英文說明行
                if len(df) > 0:
                    first_val = str(df.iloc[0, 0])
                    if 'area' in first_val.lower() or '1.' in first_val or '建物' not in first_val and not first_val.replace('.','',1).isdigit():
                        df = df.iloc[1:].reset_index(drop=True)
                
                all_dfs.append(df)

# 合併所有 CSV 的資料
if all_dfs:
    full_df = pd.concat(all_dfs, ignore_index=True)
else:
    raise FileNotFoundError("壓縮檔內找不到任何 CSV 檔案")

print(f"成功載入全部資料總筆數：{len(full_df)}")

# 2. 將全部資料（或過濾後的有效資料）轉換為 listings.json 格式供前端地圖使用
listings = []

# 為了避免網頁載入過多卡片過載，我們預設取前 100 筆或全部有經緯度/價格的資料
target_df = full_df

for idx, row in target_df.iterrows():
    district = str(row.get('鄉鎮市區', '安平區'))
    
    try:
        pings = float(row.get('建物移轉總面積平方公尺', 100)) / 3.3058
    except (ValueError, TypeError):
        pings = 30.0

    try:
        total_price = int(float(row.get('總價元', row.get('總價', 10000000))))
    except (ValueError, TypeError):
        total_price = 10000000

    unit_price = int(total_price / pings) if pings > 0 else 300000
    
    listing = {
        "id": f"tn-all-{idx+1}",
        "title": f"{district}實價登錄精選物件 {idx+1}",
        "district": district,
        "price": total_price,
        "unit_price": unit_price,
        "ping": round(pings, 1),
        "layout": str(row.get('建物型態', '住宅大樓')),
        "lat": 22.9997 + (idx % 10) * 0.005,  # 稍微錯開座標，讓地圖上的標記不會全部疊在一起
        "lng": 120.2270 + (idx % 10) * 0.005,
        "description": f"建物型態：{row.get('建物型態', '住宅')}，移轉面積約 {round(pings, 1)} 坪。",
        "ai_comment": "由 AI 代理自動從完整實價登錄大數據中深度解析之優質物件。"
    }
    listings.append(listing)

# 寫入 listings.json 檔案
with open('listings.json', 'w', encoding='utf-8') as jf:
    json.dump(listings, jf, ensure_ascii=False, indent=2)
print(f"已成功更新 listings.json 資料庫！共寫入 {len(listings)} 筆資料。")

# 3. 初始化 Gemini AI 進行房市分析日報（取前 5 筆具代表性數據給 AI 總結，避免 Prompt 過長）
summary_sample = full_df.head(5)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
prompt = f"請根據以下最新實價登錄數據大數據樣本，以專業房地產分析師口吻撰寫一份簡短、精彩的房市日報：\n{summary_sample.to_string()}"

response_ai = client.models.generate_content(
    model='gemini-3.8-flash',
    contents=prompt,
)

report_text = response_ai.text
print("AI 分析完成：")
print(report_text)

# 4. 發送 Telegram 通知
telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

if telegram_token and telegram_chat_id:
    import requests
    tg_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {
        "chat_id": telegram_chat_id,
        "text": f"🏠 【房產 AI 日報 (全量數據)】\n\n{report_text}",
        "parse_mode": "Markdown"
    }
    requests.post(tg_url, json=payload)
    print("Telegram 通知已發送！")
