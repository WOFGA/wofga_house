import os
import zipfile
import io
import requests
import pandas as pd
from google import genai

# 1. 下載內政部實價登錄 ZIP 資料
url = "https://plvr.land.moi.gov.tw//Download?type=zip&fileName=lvr_landA.zip"
print("正在從內政部下載最新台南市實價登錄資料...")
response = requests.get(url)
z = zipfile.ZipFile(io.BytesIO(response.content))

# 自動尋找壓縮檔中實際存在的 CSV 檔名，避免發生 KeyError
csv_filename = None
for filename in z.namelist():
    if filename.endswith('.csv'):
        csv_filename = filename
        break

if not csv_filename:
    raise FileNotFoundError("找不到內政部實價登錄壓縮檔中的 CSV 檔案")

with z.open(csv_filename) as f:
    df = pd.read_csv(f, low_memory=False)

# 2. 過濾台南市資料（若以代號或中文篩選）
# 內政部資料第一列通常為欄位中文說明，實際資料從第二列開始
if '鄉鎮市區' in df.columns:
    tainan_df = df[df['鄉鎮市區'].str.contains('安平|永康|中西|東區|北區|南區|安南', na=False)].head(5)
else:
    tainan_df = df.head(5)

print(f"成功過濾出筆數：{len(tainan_df)}")

# 3. 初始化 Gemini AI 進行分析
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
prompt = f"請根據以下實價登錄數據，以專業房地產分析師口吻撰寫一份簡短的台南房市日報：\n{tainan_df.to_string()}"

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
    tg_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {
        "chat_id": telegram_chat_id,
        "text": f"🏠 【台南房產 AI 日報】\n\n{report_text}",
        "parse_mode": "Markdown"
    }
    requests.post(tg_url, json=payload)
    print("Telegram 通知已發送！")
