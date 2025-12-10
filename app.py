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
default_tickers = "2330, 2603, 3231, 8069, 8358"
user_input = st.sidebar.text_area("請輸入代號 (用逗號分隔)", default_tickers)

# --- 核心邏輯函數 (升級版：自動偵測上市/上櫃) ---
def analyze_stock(ticker):
    raw_id = ticker.strip()
    # 嘗試兩種後綴：先試 .TW (上市), 再試 .TWO (上櫃)
    suffixes = ['.TW', '.TWO']
    
    stock_data = None
    final_id = ""
    
    for suffix in suffixes:
        try:
            temp_id = raw_id + suffix
            stock = yf.Ticker(temp_id)
            df = stock.history(period="5d")
            
            if len(df) > 0:
                stock_data = df
                final_id = temp_id
                break # 找到了就跳出迴圈
        except:
            continue
            
    # 如果試了兩種都沒資料，就回傳 None
    if stock_data is None:
        return None

    # --- 開始分析 ---
    try:
        price = stock_data['Close'].iloc[-1]
        volume_share = stock_data['Volume'].iloc[-1] 
        volume = volume_share / 1000 # 換算成張
        
        # 判斷流動性燈號 (羅伯 SOP v3.3)
        liquidity = "未知"
        tactics = "觀察"
        color = "⚪"
        
        if price < 50: # 銅板股
            if volume < 3000:
                color = "🩸"
                liquidity = "低流動 (垃圾)"
                tactics = "刪除"
            elif 3000 <= volume < 10000:
                color = "🟡"
                liquidity = "正常"
                tactics = "波段"
            else:
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
            else:
                color = "🟢"
                liquidity = "高流動"
                tactics = "狼性追擊"
                
        else: # 千金股
            if volume < 300:
                color = "🩸"
                liquidity = "低流動 (危險)"
                tactics = "刪除"
            elif 300 <= volume < 800:
                color = "🟡"
                liquidity = "正常"
                tactics = "波段"
            else:
                color = "🟢"
                liquidity = "高流動"
                tactics = "狼性追擊"

        return {
            "代號": raw_id, # 顯示原始輸入的代號就好
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
    
    # 進度條
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(tickers):
        clean_ticker = ticker.strip()
        if clean_ticker:
            status_text.text(f"正在掃描: {clean_ticker} ...")
            data = analyze_stock(clean_ticker)
            if data:
                results.append(data)
        progress_bar.progress((i + 1) / len(tickers))
    
    status_text.empty() # 清除狀態文字
        
    if results:
        df_res = pd.DataFrame(results)
        st.table(df_res)
    else:
        st.warning("查無資料，請確認代號是否正確。")
