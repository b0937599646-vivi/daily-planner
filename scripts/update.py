"""每天抓台中天氣和新聞，寫進 data.json。不用 Claude。只用 Python 內建功能。"""
import json, re, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
LAT, LON = 24.15, 120.67  # 台中
NEWS_COUNT = 8
UA = {"User-Agent": "daily-planner/1.0"}
CODE = {0:"晴",1:"大致晴朗",2:"多雲時晴",3:"陰天",45:"有霧",48:"有霧",51:"毛毛雨",53:"毛毛雨",55:"毛毛雨",61:"小雨",63:"中雨",65:"大雨",71:"小雪",73:"中雪",75:"大雪",80:"陣雨",81:"陣雨",82:"強陣雨",95:"雷雨",96:"雷雨",99:"強雷雨"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read()

def weather():
    u = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Asia%2FTaipei&forecast_days=1"
    d = json.loads(get(u))["daily"]
    rain = d["precipitation_probability_max"][0]
    umbrella = "" if rain is None else "要帶傘" if rain >= 50 else "可帶備用傘" if rain >= 30 else "不用帶傘"
    return {"temp": f'{round(d["temperature_2m_min"][0])}–{round(d["temperature_2m_max"][0])}°C',
            "rain": "" if rain is None else f"{rain}%", "umbrella": umbrella,
            "summary": CODE.get(d["weather_code"][0], "")}

def clean(title):
    """標題常帶「| 作者 | 分類」，只留最長的那段（真正的標題）。"""
    return max(re.split(r"\s*[|｜]\s*", title), key=len).strip()

def news():
    root = ET.fromstring(get("https://news.google.com/rss?hl=zh-TW&gl=TW&ceid=TW:zh-Hant"))
    out = []
    for i in root.iterfind("./channel/item"):
        src = i.findtext("source") or ""
        title = (i.findtext("title") or "").strip()
        if src and title.endswith(" - " + src):
            title = title[: -len(src) - 3]
        title = clean(title)
        link = i.findtext("link") or ""
        if title and link.startswith("https://"):
            out.append({"title": title, "source": src, "url": link})
        if len(out) >= NEWS_COUNT:
            break
    return out

def main():
    now = datetime.now(timezone(timedelta(hours=8)))
    try:
        with open("data.json", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    errors, ok = [], False
    for key, fn in (("weather", weather), ("news", news)):
        try:
            data[key] = fn(); ok = True
        except Exception as e:  # 一邊失敗時保留舊資料，另一邊照常更新
            errors.append(f"{key}: {e}")
    data["errors"] = errors
    if ok:
        data["date"], data["updated"] = now.strftime("%Y-%m-%d"), now.strftime("%H:%M")
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("errors:", errors)
    raise SystemExit(0 if ok else 1)

if __name__ == "__main__":
    main()
