import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 頁面標題
st.set_page_config(page_title="AI 進階台股看板", layout="wide")
st.title("🚀 AI 台股個人化看板 v2.6")

# 左側輸入欄位
with st.sidebar:
    st.header("參數設定")
    raw_input = st.text_input("輸入台股代號 (例: 2330)", value="")
    
    if raw_input.isdigit():
        stock_id = f"{raw_input}.TW"
    else:
        stock_id = raw_input.upper()

    buy_price = st.number_input("您的購股均價", min_value=0.0, step=0.1, value=0.0)
    target_budget = st.number_input("預計購買金額 (台幣)", min_value=0, step=1000, value=100000)

# 只有當有輸入代號時才執行後續邏輯
if raw_input:
    try:
        ticker = yf.Ticker(stock_id)
        # 增加讀取天數確保 MA20 計算準確
        df = ticker.history(period="400d")[['Close']]
        
        if not df.empty:
            df['MA20'] = df['Close'].rolling(window=20).mean()
            recent_df = df.iloc[-360:].copy()
            
            curr_price = float(recent_df['Close'].iloc[-1])
            ma20_curr = float(recent_df['MA20'].iloc[-1])
            high_360 = float(recent_df['Close'].max())
            low_360 = float(recent_df['Close'].min())
            
            # --- 頂部指標 ---
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("當前現價", f"{curr_price:.2f}")
                if buy_price > 0:
                    profit_pct = ((curr_price - buy_price) / buy_price) * 100
                    profit_val = curr_price - buy_price
                    st.metric("個人持股損益", f"{profit_pct:.2f}%", f"{profit_val:.2f}")
                else:
                    st.caption("👈 請輸入均價計算損益")

            with col2:
                st.metric("360D 最高價", f"{high_360:.2f}")
                st.metric("高點跌幅", f"{((curr_price - high_360) / high_360) * 100:.2f}%")

            with col3:
                st.metric("360D 最低價", f"{low_360:.2f}")
                st.metric("低點漲幅", f"+{((curr_price - low_360) / low_360) * 100:.2f}%")
            
            with col4:
                position = ((curr_price - low_360) / (high_360 - low_360)) * 100
                st.metric("區間相對位置", f"{position:.1f}%")
                st.caption("0%=最低, 100%=最高")

            # --- AI 股市建議區 ---
            st.divider()
            st.subheader("🤖 AI 技術面分析建議")
            if curr_price > ma20_curr * 1.05:
                st.warning("🔥 **強勢過熱**：股價顯著高於月線，需注意短期回檔風險。")
            elif curr_price > ma20_curr:
                st.success("✅ **趨勢偏多**：股價站在月線之上，短線趨勢樂觀。")
            elif curr_price < ma20_curr * 0.95:
                st.error("⚠️ **超跌預警**：股價遠低於月線，建議靜待止跌訊號。")
            else:
                st.info("⚖️ **區間震盪**：股價與月線糾結，方向尚不明朗。")

            # --- 趨勢圖表 ---
            st.subheader("📅 股價與月線趨勢")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=recent_df.index, y=recent_df['Close'], name='收盤價', line=dict(color='royalblue')))
            fig.add_trace(go.Scatter(x=recent_df.index, y=recent_df['MA20'], name='20日月線', line=dict(color='orange', dash='dot')))
            fig.update_layout(height=400, template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

            # --- 最近五日變動 ---
            st.subheader("📊 最近五日變動分析")
            inst_df = recent_df[['Close']].tail(6).copy()
            inst_df['當日價差'] = inst_df['Close'].diff()
            
            display_inst = inst_df.tail(5).reset_index().copy()
            display_inst['Date'] = display_inst['Date'].dt.strftime('%Y-%m-%d')
            display_inst['趨勢判斷'] = display_inst['當日價差'].apply(lambda x: "🔴 買盤" if x > 0 else ("🟢 賣壓" if x < 0 else "⚪ 平盤"))
            
            # 格式化顯示
            display_inst['Close'] = display_inst['Close'].map('{:.2f}'.format)
            display_inst['當日價差'] = display_inst['當日價差'].map('{:+.2f}'.format)
            
            display_inst = display_inst.iloc[::-1]
            display_inst.columns = ['交易日期', '收盤價', '當日價差', '趨勢判斷']
            st.table(display_inst)

            # --- 底部資訊與新聞連結 ---
            st.divider()
            st.subheader("📰 相關外部連結")
            # 修正後的網址格式
            st.markdown(f"""
            🔗 [Yahoo 股市 - {raw_input}](https://yahoo.com{stock_id})  
            🔗 [鉅亨網 - {raw_input}](https://cnyes.com{raw_input})
            """)
            
            shares = int(target_budget / curr_price) if target_budget > 0 else 0
            st.info(f"💰 預算 {target_budget:,} 元約可購買： **{shares:,}** 股")
        else:
            st.error("查無資料，請確認代號是否正確。")

    except Exception as e:
        st.error(f"讀取失敗。原因: {e}")
else:
    st.info("💡 請在左側側邊欄輸入「台股代號」開始分析（例如：2330）。")
