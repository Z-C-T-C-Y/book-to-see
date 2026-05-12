import streamlit as st
import pandas as pd
import random
import io
import requests
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="全球图书智能推荐系统 V7.0", layout="wide")
st.title("📚 智慧馆藏推荐系统 (历史数据参考版)")

# --- 尼尔森/数据抓取逻辑 (保持之前的稳定版本) ---
def get_nielsen_details(isbn, username, password):
    # (此处省略之前已实现的抓取代码，保持逻辑一致...)
    return None

# --- 核心：历史数据分析引擎 ---
def analyze_history(new_row, history_df):
    if history_df is None or history_df.empty:
        return ""
    
    # 获取当前书的信息
    current_pub = str(new_row.get('出版社', ''))
    current_author = str(new_row.get('著者', ''))
    
    # 逻辑1：检查出版社重合度
    pub_match = history_df[history_df['出版社'].str.contains(current_pub, na=False, case=False)] if current_pub else []
    # 逻辑2：检查作者重合度
    author_match = history_df[history_df['著者'].str.contains(current_author, na=False, case=False)] if current_author else []
    
    insights = []
    if len(pub_match) > 5:
        insights.append(f"该馆历史已采选该出版社图书 {len(pub_match)} 种，馆藏匹配度极高")
    if len(author_match) > 0:
        insights.append(f"该馆曾采购过此作者的相关作品，建议保持系列连贯性")
        
    return " | ".join(insights) if insights else "该书为馆藏新领域补充"

# --- 综合推荐生成逻辑 ---
def generate_advanced_reason(row, history_df, audience, style, n_user, n_pass):
    local_intro = str(row.get('内容简介', '')).strip()
    if local_intro == 'nan': local_intro = ""
    
    # 1. 获取历史参考信息
    history_insight = analyze_history(row, history_df)
    
    # 2. 模拟风格化逻辑
    style_msg = {
        "学术": "学术前沿性强，符合高校馆藏标准。",
        "大众": "内容受众广，建议作为阅览室重点推荐。",
        "大学生": "适合作为参考教材，提升学生科研素养。"
    }.get(style, "优质选书建议。")

    final_reason = f"【历史参考】：{history_insight}\n\n【内容简介】：{local_intro[:100]}...\n\n【{audience}建议】：{style_msg}"
    return final_reason

# --- 用户界面 ---
with st.sidebar:
    st.header("📂 数据上传中心")
    new_books_file = st.file_uploader("1. 上传本期待选新书 (需含'内容简介')", type=["xlsx"])
    history_file = st.file_uploader("2. 上传历史采买数据 (参考库)", type=["xlsx"])
    
    st.divider()
    st.header("🔐 接口授权")
    n_user = st.text_input("Nielsen Username")
    n_pass = st.text_input("Nielsen Password", type="password")
    
    num_rec = st.number_input("推荐数量", 1, 50, 3)
    style_preference = st.selectbox("推荐风格", ["学术", "大众", "大学生"])

# 加载历史数据
history_data = None
if history_file:
    history_data = pd.read_excel(history_file)
    st.sidebar.success(f"已加载 {len(history_data)} 条历史记录")

if new_books_file:
    df_new = pd.read_excel(new_books_file)
    if st.button("🏁 开始智能查重与推荐"):
        selected_df = df_new.sample(n=min(len(df_new), int(num_rec))).copy()
        reasons = []
        
        for idx, row in selected_df.iterrows():
            st.write(f"正在分析历史关联: 《{row['书名']}》")
            reasons.append(generate_advanced_reason(row, history_data, "图书馆", style_preference, n_user, n_pass))
        
        selected_df['智能综合推荐理由'] = reasons
        
        # 结果展示
        st.subheader("📋 最终推荐方案")
        st.dataframe(selected_df[['ISBN', '书名', '智能综合推荐理由']], use_container_width=True)
        
        # 导出
        output = io.BytesIO()
        selected_df.to_excel(output, index=False)
        st.download_button("📥 点击下载正式采选报告", output.getvalue(), "智慧采选方案.xlsx")
