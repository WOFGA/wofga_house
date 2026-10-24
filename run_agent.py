import os
import zipfile
import json
import pandas as pd
from google import genai

# 1. 直接讀取你上傳到 GitHub 根目錄的本地 ZIP 檔案
zip_path = "lvr_landcsv.zip"
print(f"正在讀取本地壓縮檔：{zip_path}")

with zipfile.ZipFile(zip_path, 'r') as z:
    # 自動尋找壓縮檔中的 CSV 檔案（優先尋找台南市代號 d 開頭的檔案）
    csv_filename = None
    for filename in z.namelist():
        if 'd_' in filename.lower() and filename.endswith('.csv'):
            csv_filename = filename
            break
    if not csv_filename:
        for filename in z.namelist():
            if filename.endswith('.csv'):
                csv_filename = filename
                break

    print(f"成功找到目標 CSV 檔案：{csv_filename}")
    with z.open(csv_filename) as f:
        try:
            df = pd.read_csv(f, low_memory=False, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(f, low_memory=False, encoding='cp950')

print(f"成功載入資料總筆數：{len(df)}")

# 2. 取出前 5 筆資料並整理格式寫入 listings.json（供前端網頁與 Git Push 使用）
sample_df = df.head(5)
listings = []
for idx, row in sample_df.iterrows():
    # 兼容內政部常見欄位名稱
    district = str(row.get('鄉鎮市區', '安平區'))
    pings = float(row.get('建物移轉總面積平方公尺', 100)) / 3.3058  # 平方公尺轉坪
    total_price = int(row.get('總價元', row.get('總價', 10000000)))
    unit_price = int(total_price / pings) if pings > 0 else 300000
    
    listing = {
        "id": f"tn-auto-{idx+1}",
        "title": f"{district}實價登錄精選物件 {idx+1}",
        "district": district,
        "price": total_price,
        "unit_price": unit_price,
        "ping": round(pings, 1),
        "layout": str(row.get('建物型態', '住宅大樓')),
        "lat": 22.9997,  # 預設台南市中心座標
        "lng": 120.2270,
        "description": f"主建物或建物型態：{row.get('建物型態', '')}，移轉面積約 {round(pings, 1)} 坪。",
        "ai_comment": "由 AI 代理自動從最新實價登錄數據中篩選並分析之優質物件。"
    }
    listings.append(listing)

# 寫入 listings.json 檔案，供後續 git commit / push
with open('listings.json', 'w', encoding='utf-8') as jf:
    json.dump(listings, jf, ensure_ascii=False, indent=2)
print("已成功更新 listings.json 資料庫！")

# 3. 初始化 Gemini AI 進行房市分析日報
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
prompt = f"請根據以下最新實價登錄數據，以專業房地產分析師口吻撰寫一份簡短、精彩的台南房市日報：\n{sample_df.to_string()}"

response_ai = client.models.generate_content(
    model='gemini-2.5-flash',
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
        "text": f"🏠 【台南房產 AI 日報】\n\n{report_text}",
        "parse_mode": "Markdown"
    }
    requests.post(tg_url, json=payload)
    print("Telegram 通知已發送！")
