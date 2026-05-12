import streamlit as st
import pandas as pd
import random
import io
import requests
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="全球图书智能推荐系统 V6.0", layout="wide")
st.title("📚 全球图书推荐系统 (本地简介 + 网上数据综合版)")

# --- 尼尔森深度解析引擎 ---
def get_nielsen_details(isbn, username, password):
    login_url = "https://www.nielsenbookdataonline.com/bdol/auth/login.do"
    search_url = "https://www.nielsenbookdataonline.com/bdol/auth/quickfind.do"
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        session.post(login_url, data={'username': username, 'password': password}, headers=headers, timeout=10)
        res = session.post(search_url, data={'quicksearch': isbn}, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # 查找 Description 或 Review
            for tag in soup.find_all(['p', 'td', 'span']):
                if re.search(r'(Description|Review):', tag.get_text(), re.I):
                    return tag.get_text(strip=True).split(':', 1)[-1]
    except:
        return None
    return None

# --- 日文书数据引擎 ---
def get_japanese_data(isbn):
    url = f"https://api.openbd.jp/v1/get?isbn={isbn}"
    try:
        res = requests.get(url, timeout=8)
        data = res.json()
        if data and data[0]:
            return data[0].get('summary', {}).get('description', "")
    except:
        return None

# --- 综合推荐生成逻辑 ---
def generate_combined_reason(row, audience, style, n_user, n_pass):
    isbn = str(row['ISBN']).replace('-', '').strip()
    local_intro = str(row.get('内容简介', '')).strip()
    if local_intro == 'nan': local_intro = ""
    
    online_info = None
    # 联网获取补充信息
    if isbn.startswith('9784') or isbn.startswith('4'):
        online_info = get_japanese_data(isbn)
    elif n_user and n_pass:
        online_info = get_nielsen_details(isbn, n_user, n_pass)
    
    # 综合内容源
    combined_content = local_intro
    if online_info and online_info not in local_intro:
        combined_content += " | 补充信息: " + online_info[:150]
    
    # 风格化润色
    style_suffix = {
        "学术": "该书论证严密，具有极高的学术价值，建议专业人士研读。",
        "大众": "本书深入浅出，是本年度非常值得推荐的‘种草’好书。",
        "大学生": "推荐给学生群体，对专业学习和视野拓展大有裨益。",
        "低龄儿童": "图文精彩，适合亲子阅读及启蒙教育。"
    }.get(style, "值得关注。")

    final_reason = f"【内容综合】{combined_content if combined_content else '根据书名及作者信息分析'}。\n\n【{audience}推荐】：{style_suffix}"
    return final_reason

# --- 界面展示 ---
with st.sidebar:
    st.header("🔐 尼尔森授权")
    n_user = st.text_input("Username")
    n_pass = st.text_input("Password", type="password")
    st.divider()
    uploaded_file = st.file_uploader("上传 Excel (需含'内容简介'列)", type=["xlsx"])
    num_rec = st.number_input("推荐数量", 1, 50, 3)
    target_audience = st.selectbox("目标受众", ["图书馆", "普通大众"])
    style_preference = st.selectbox("推荐风格", ["学术", "大众", "大学生", "低龄儿童"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip() # 清理空格
    
    if st.button("🚀 生成综合推荐报表"):
        if '内容简介' not in df.columns:
            st.error("表格中缺少‘内容简介’列，请检查！")
        else:
            selected_df = df.sample(n=min(len(df), int(num_rec))).copy()
            reasons = []
            bar = st.progress(0)
            for i, (idx, row) in enumerate(selected_df.iterrows()):
                st.write(f"正在综合分析: 《{row['书名']}》")
                reasons.append(generate_combined_reason(row, target_audience, style_preference, n_user, n_pass))
                bar.progress((i + 1) / len(selected_df))
            
            selected_df['智能综合推荐理由'] = reasons
            st.success("报表已生成！")
            st.dataframe(selected_df[['ISBN', '书名', '内容简介', '智能综合推荐理由']], use_container_width=True)
            
            output = io.BytesIO()
            selected_df.to_excel(output, index=False)
            st.download_button("📥 下载 Excel 结果", output.getvalue(), "综合推荐表.xlsx")
