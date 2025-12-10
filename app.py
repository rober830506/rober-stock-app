import streamlit as st
import yfinance as yf
import pandas as pd

# --- 設定網頁標題 ---
st.set_page_config(page_title="羅伯長官選股雷達", layout="wide")

# --- 側邊欄：設定與輸入 ---
st.sidebar.header("⚙️ 參數設定")

# 1. 取得大盤資訊 (加權指數 ^TWII)
try:
    twii = yf.Ticker("^TWII")
    # 抓取最近 3 個月的資料來計算月線
    hist = twii.history(period="3mo")
    
    if len(hist) > 20:
        current_price = hist['Close'].iloc[-1]
        ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        
        st.sidebar.markdown("### 📊 大盤 (加權指數)")
        st.sidebar.write(f"目前點數: {current_price:.2f}")
        st.sidebar.write(f"月線 (20MA): {ma20:.2f}")
        
        if current_price > ma20:
            market_status = "BULL"
            st.sidebar.success("🔥 多頭趨勢，積極操作")
        else:
            market_status = "BEAR"
            st.sidebar.error("⚠️ 空頭趨勢，保守操作")
    else:
        st.sidebar.warning("無法取得足夠的大盤資料")
        market_status = "UNKNOWN"

except Exception as e:
    st.sidebar.error(f"大盤資料讀取失敗: {e}")
    market_status = "UNKNOWN"

# 2. 股票代號輸入
st.sidebar.markdown("---")
st.sidebar.subheader("🔎 輸入股票代號")
default_tickers = "2330, 2603, 3231, 2317, 3035"
user_input = st.sidebar.text_area("請輸入代號 (用逗號分隔)", default_tickers)

# --- 核心邏輯函數 ---
def analyze_stock(ticker):
    # 處理代號，加上 .TW
    stock_id = ticker.strip()
    if not stock_id.endswith('.TW'):
        stock_id = stock_id + '.TW'
    
    try:
        stock = yf.Ticker(stock_id)
        # 取得即時/今日資料
        df = stock.history(period="5d")
        
        if len(df) < 1:
            return None
        
        price = df['Close'].iloc[-1]
        # 成交量 (有些資料源是股數，這裡除以1000換算成張數)
        volume_share = df['Volume'].iloc[-1] 
        volume = volume_share / 1000 # 換算成張
        
        # 判斷流動性燈號 (羅伯 SOP v3.3)
        liquidity = "未知"
        tactics = "觀察"
        color = "⚪" # 預設白燈
        
        # 邏輯判斷
        if price < 50: # 銅板股
            if volume < 3000:
                color = "🩸"
                liquidity = "低流動 (垃圾)"
                tactics = "刪除"
            elif 3000 <= volume < 10000:
                color = "🟡"
                liquidity = "正常"
                tactics = "波段"
            else: # > 10000
                color = "🟢"
                liquidity = "高流動"
                tactics = "狼性追擊"
                
        elif 50 <= price < 1000: # 中高價股
            if volume < 1000:
                color = "🩸"
                liquidity = "低流動 (危險)"
                tactics = "刪除"
            elif 1000 <= volume < 3000:
                color = "🟡"
                liquidity = "正常"
                tactics = "波段"
            else: # > 3000
                color = "🟢"
                liquidity = "高流動"
                tactics = "狼性追擊"
                
        else: # 千金股/高價股 (Price >= 1000)
            if volume < 300:
                color = "🩸"
                liquidity = "低流動 (危險)"
                tactics = "刪除"
            elif 300 <= volume < 800:
                color = "🟡"
                liquidity = "正常"
                tactics = "波段"
            else: # > 800
                color = "🟢"
                liquidity = "高流動"
                tactics = "狼性追擊"

        return {
            "代號": ticker.strip(),
            "股價": f"{price:.2f}",
            "成交量(張)": f"{int(volume):,}",
            "燈號": color,
            "流動性狀態": liquidity,
            "戰術建議": tactics
        }

    except Exception as e:
        return None

# --- 主畫面顯示 ---
st.title("🚀 羅伯長官的台股戰情室")

if market_status == "BEAR":
    st.error("🚨 警告：目前大盤位於月線之下，屬於空頭趨勢，請嚴格控制部位！")
elif market_status == "BULL":
    st.success("🌈 提示：目前大盤位於月線之上，多頭趨勢，可積極選股。")

st.markdown("### 📋 掃描結果")

if st.button("開始掃描"):
    tickers = user_input.split(',')
    results = []
    
    progress_bar = st.progress(0)
    
    for i, ticker in enumerate(tickers):
        if ticker.strip():
            data = analyze_stock(ticker)
            if data:
                results.append(data)
        progress_bar.progress((i + 1) / len(tickers))
        
    if results:
        df_res = pd.DataFrame(results)
        st.table(df_res)
    else:
        st.warning("查無資料，請檢查代號是否正確。")
