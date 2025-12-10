import streamlit as st
import yfinance as yf
import pandas as pd

# --- 設定網頁標題 ---
st.set_page_config(page_title="羅伯長官選股雷達 v2.1", layout="wide")

# --- 戰區清單 (V2.1 全面擴充版) ---
SECTOR_LISTS = {
    "🔹 自選模式 (手動輸入)": [], 
    
    "🔥 AI 伺服器與組裝 (代工五哥)": "2382, 3231, 2356, 6669, 2376, 2301, 2317, 2421",
    
    "⚡ PCB 與銅箔基板 (AI 高速傳輸)": "2383, 6274, 6213, 3037, 2368, 2313, 3044, 8046, 3189, 4958",
    
    "🛠️ CoWoS 與儀器設備 (AI 軍火庫)": "3131, 3583, 3680, 6187, 2404, 5443, 6640, 3413, 6196, 3587",
    
    "🔌 重電與電纜 (能源缺口概念)": "1513, 1519, 1503, 1514, 1605, 1609, 1603, 1616, 6806",
    
    "✈️ 軍工與無人機 (國防自主)": "8033, 2634, 2645, 5284, 8222, 4572, 2630, 3005",
    
    "🚢 散裝航運 (BDI 指數)": "2606, 2637, 2605, 2612, 5608, 2641, 2614",
    
    "📦 貨櫃航運 (航海王)": "2603, 2609, 2615",
    
    "🏆 台灣 50 (權值護盤軍)": "2330, 2317, 2454, 2308, 2881, 2412, 2303, 2882, 1216, 2002"
}

# --- 側邊欄：設定與輸入 ---
st.sidebar.header("⚙️ 戰術控制台")

# 1. 大盤資訊
try:
    twii = yf.Ticker("^TWII")
    hist = twii.history(period="3mo")
    if len(hist) > 20:
        current_price = hist['Close'].iloc[-1]
        ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        st.sidebar.markdown(f"### 📊 加權指數: {current_price:.0f}")
        st.sidebar.markdown(f"月線 (20MA): {ma20:.0f}")
        if current_price > ma20:
            market_status = "BULL"
            st.sidebar.success("🔥 多頭趨勢，積極操作")
        else:
            market_status = "BEAR"
            st.sidebar.error("⚠️ 空頭趨勢，保守操作")
    else:
        market_status = "UNKNOWN"
except:
    st.sidebar.warning("無法連線大盤")
    market_status = "UNKNOWN"

st.sidebar.markdown("---")

# 2. 戰區選擇
st.sidebar.subheader("🎯 選擇掃描戰區")
selected_sector = st.sidebar.selectbox("請選擇清單：", list(SECTOR_LISTS.keys()))

# 根據選擇自動填入代碼
if "自選" in selected_sector:
    default_text = "2330, 3231, 8069"
    user_input = st.sidebar.text_area("輸入代號 (逗號分隔)", default_text, height=150)
    target_list = user_input
else:
    # 顯示該戰區的股票，並允許長官手動增減
    default_text = SECTOR_LISTS[selected_sector]
    user_input = st.sidebar.text_area("戰區名單 (可手動修改)", default_text, height=150)
    target_list = user_input

# --- 核心邏輯 (SOP v3.3 + 上市櫃自動判斷) ---
def analyze_stock(ticker):
    raw_id = ticker.strip()
    if not raw_id: return None
    
    # 自動偵測 .TW 或 .TWO
    suffixes = ['.TW', '.TWO']
    stock_data = None
    
    for suffix in suffixes:
        try:
            temp_id = raw_id + suffix
            stock = yf.Ticker(temp_id)
            df = stock.history(period="5d")
            if len(df) > 0:
                stock_data = df
                break
        except:
            continue
            
    if stock_data is None: return None

    try:
        price = stock_data['Close'].iloc[-1]
        vol_share = stock_data['Volume'].iloc[-1] 
        volume = vol_share / 1000 
        
        # SOP v3.3 燈號邏輯
        color = "⚪"
        liquidity = "未知"
        tactics = "觀察"
        
        if price < 50:
            if volume < 3000: color, liquidity, tactics = "🩸", "低流動(垃圾)", "刪除"
            elif volume < 10000: color, liquidity, tactics = "🟡", "正常", "波段"
            else: color, liquidity, tactics = "🟢", "高流動", "狼性追擊"
        elif price < 1000:
            if volume < 1000: color, liquidity, tactics = "🩸", "低流動(危險)", "刪除"
            elif volume < 3000: color, liquidity, tactics = "🟡", "正常", "波段"
            else: color, liquidity, tactics = "🟢", "高流動", "狼性追擊"
        else:
            if volume < 300: color, liquidity, tactics = "🩸", "低流動(危險)", "刪除"
            elif volume < 800: color, liquidity, tactics = "🟡", "正常", "波段"
            else: color, liquidity, tactics = "🟢", "高流動", "狼性追擊"

        return {
            "代號": raw_id,
            "股價": price, 
            "成交量": int(volume),
            "燈號": color,
            "狀態": liquidity,
            "戰術": tactics
        }
    except:
        return None

# --- 主畫面 ---
st.title(f"🚀 羅伯長官戰情室 - {selected_sector.split(' ')[1]}") # 只顯示名稱部分

if st.button("🚀 啟動雷達掃描", type="primary"):
    tickers = target_list.split(',')
    results = []
    
    # 進度條
    my_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(tickers):
        clean_ticker = ticker.strip()
        if clean_ticker:
            status_text.text(f"正在鎖定目標: {clean_ticker} ...")
            data = analyze_stock(clean_ticker)
            if data:
                results.append(data)
        my_bar.progress((i + 1) / len(tickers))
    
    status_text.empty()
    my_bar.empty()
        
    if results:
        df = pd.DataFrame(results)
        # 排序：優先顯示「高流動」的狼性目標
        # 我們加個權重排序：高流動(3) > 正常(2) > 低流動(1)
        sort_map = {"高流動": 3, "正常": 2, "低流動(垃圾)": 1, "低流動(危險)": 1, "未知": 0}
        df['權重'] = df['狀態'].map(lambda x: sort_map.get(x, 0))
        df = df.sort_values(by=['權重', '成交量'], ascending=[False, False]).drop(columns=['權重'])

        st.dataframe(
            df.style.format({"股價": "{:.2f}", "成交量": "{:,}"}),
            height=600,
            use_container_width=True
        )
    else:
        st.warning("⚠️ 掃描完畢，無有效目標。")
