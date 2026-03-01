import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import calendar

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="369 ELITE V33", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;600&display=swap');
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .stTabs [data-testid="stVerticalBlock"] > div { animation: fadeIn 0.5s ease-out forwards; }
    .stApp { background: #05070a; color: #e6edf3; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Orbitron'; color: #00ffcc; text-align: center; text-shadow: 0 0 20px rgba(0,255,204,0.4); padding: 10px 0 5px 0; }
    .cal-card { border-radius: 8px; padding: 15px; text-align: center; min-height: 110px; transition: 0.3s; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 10px; }
    .cal-win { background: linear-gradient(135deg, rgba(45, 101, 74, 0.9), rgba(20, 50, 40, 0.9)); border-top: 4px solid #34d399; }
    .cal-loss { background: linear-gradient(135deg, rgba(127, 45, 45, 0.9), rgba(60, 20, 20, 0.9)); border-top: 4px solid #ef4444; }
    .cal-be { background: linear-gradient(135deg, rgba(180, 130, 40, 0.9), rgba(80, 60, 20, 0.9)); border-top: 4px solid #fbbf24; }
    .cal-empty { background: #161b22; opacity: 0.3; }
    div[data-testid="stMetric"] { background: rgba(22, 27, 34, 0.7) !important; border: 1px solid #30363d !important; backdrop-filter: blur(5px); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ENGINE ---
def get_db_connection():
    return sqlite3.connect('elite_final_v33.db', check_same_thread=False)

conn = get_db_connection()
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS trades 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, pair TEXT, 
              outcome TEXT, pnl REAL, rr REAL, balance REAL, mindset TEXT, setup TEXT)''')
conn.commit()

# --- 3. DATA LOADING (Fixed Cache Logic) ---
def load_data():
    temp_df = pd.read_sql_query("SELECT * FROM trades", conn)
    if not temp_df.empty:
        temp_df['date_dt'] = pd.to_datetime(temp_df['date'])
        temp_df = temp_df.sort_values('date_dt')
        temp_df['cum_pnl'] = temp_df['pnl'].cumsum()
        temp_df['equity_curve'] = temp_df['balance'].iloc[0] + temp_df['cum_pnl']
    return temp_df

df = load_data()
current_balance = df['equity_curve'].iloc[-1] if not df.empty else 0.0
total_pnl = df['pnl'].sum() if not df.empty else 0.0

# --- 4. HEADER & EQUITY ---
st.markdown('<h1 class="main-title">369 TRACKER PRO V33</h1>', unsafe_allow_html=True)
col_eq1, col_eq2, col_eq3 = st.columns([1, 2, 1])
with col_eq2:
    st.metric(label="CURRENT EQUITY", value=f"${current_balance:,.2f}", delta=f"${total_pnl:,.2f}")

tabs = st.tabs(["🚀 TERMINAL", "📅 CALENDAR LOG", "📊 MONTHLY %", "🧬 ANALYZERS", "📜 JOURNAL"])

# --- TAB 1: TERMINAL ---
with tabs[0]:
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.form("entry_v33", clear_on_submit=True):
            st.subheader("Log Execution")
            bal_in = st.number_input("Initial Balance ($)", value=1000.0, format="%.2f")
            d_in = st.date_input("Date", datetime.now())
            asset = st.text_input("Pair", "NAS100").upper()
            res = st.selectbox("Outcome", ["WIN", "LOSS", "BE"])
            p_val = st.number_input("P&L ($)", value=0.0, format="%.2f")
            r_val = st.number_input("RR Ratio", value=0.0, format="%.2f")
            setup = st.text_input("Setup").upper()
            mind = st.selectbox("Mindset", ["Focused", "Impulsive", "Revenge", "Bored"])
            if st.form_submit_button("LOCK"):
                c.execute("INSERT INTO trades (date, pair, outcome, pnl, rr, balance, mindset, setup) VALUES (?,?,?,?,?,?,?,?)",
                          (str(d_in), asset, res, p_val, r_val, bal_in, mind, setup))
                conn.commit()
                st.rerun() # Refresh to show new data
    with c2:
        if not df.empty:
            fig_eq = px.line(df, x='date_dt', y='equity_curve', title="📈 ACCOUNT GROWTH")
            fig_eq.update_traces(line_color='#00ffcc', fill='tozeroy', markers=True)
            fig_eq.update_layout(template="plotly_dark", xaxis_title="Time", yaxis_title="Balance")
            st.plotly_chart(fig_eq, use_container_width=True)

# --- TAB 2: CALENDAR LOG ---
with tabs[1]:
    if not df.empty:
        today = datetime.now()
        cal = calendar.monthcalendar(today.year, today.month)
        cols_h = st.columns(7)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, d_n in enumerate(days): cols_h[i].markdown(f"<p style='text-align:center; color:#8b949e'>{d_n}</p>", unsafe_allow_html=True)
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0: cols[i].markdown('<div class="cal-card cal-empty"></div>', unsafe_allow_html=True)
                else:
                    curr_d = datetime(today.year, today.month, day).date()
                    day_data = df[df['date_dt'].dt.date == curr_d]
                    p_s = day_data['pnl'].sum()
                    cnt = len(day_data)
                    style = "cal-win" if cnt > 0 and p_s > 0 else "cal-loss" if cnt > 0 and p_s < 0 else "cal-be" if cnt > 0 else "cal-empty"
                    pnl_txt = f"${p_s:.2f}" if cnt > 0 else ""
                    cols[i].markdown(f'<div class="cal-card {style}"><div class="cal-date">{day}</div><div class="cal-pnl">{pnl_txt}</div><div style="font-size:0.7rem">{cnt if cnt>0 else ""} Trades</div></div>', unsafe_allow_html=True)

# --- TAB 3: MONTHLY % ---
with tabs[2]:
    if not df.empty:
        df['month_year'] = df['date_dt'].dt.to_period('M').astype(str)
        m_s = df.groupby('month_year').agg({'pnl': 'sum', 'balance': 'first'}).reset_index()
        m_s['pct'] = (m_s['pnl'] / m_s['balance']) * 100
        fig_m = px.bar(m_s, x='month_year', y='pct', color='pct', color_continuous_scale=['#ef4444', '#34d399'])
        st.plotly_chart(fig_m, use_container_width=True)

# --- TAB 4: ANALYZERS (Gauge Score) ---
with tabs[3]:
    if not df.empty:
        # Consistency Logic
        avg_w = df[df['pnl'] > 0]['pnl'].mean() if not df[df['pnl'] > 0].empty else 1
        avg_l = abs(df[df['pnl'] < 0]['pnl'].mean()) if not df[df['pnl'] < 0].empty else 1
        wr = len(df[df['outcome']=='WIN']) / len(df)
        score = min((avg_w / avg_l) * wr * 10, 10.0)

        fig_g = go.Figure(go.Indicator(
            mode="gauge+number", value=score, domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [0, 10]}, 'bar': {'color': "#00ffcc"}},
            title={'text': "Consistency Score / 10"}))
        st.plotly_chart(fig_g, use_container_width=True)

        ca, cb = st.columns(2)
        with ca: st.plotly_chart(px.scatter(df, x='rr', y='pnl', color='outcome', title="Risk Tracker", template="plotly_dark"), use_container_width=True)
        with cb: st.plotly_chart(px.bar(df.groupby('mindset')['pnl'].sum().reset_index(), x='mindset', y='pnl', title="Mindset Tracker", template="plotly_dark"), use_container_width=True)

# --- TAB 5: JOURNAL (Professional Colors) ---
with tabs[4]:
    if not df.empty:
        st.dataframe(df.sort_values('date_dt', ascending=False).style.format({"pnl": "{:.2f}", "rr": "{:.2f}"}), use_container_width=True)
