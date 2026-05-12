import streamlit as st
import pandas as pd
import random
import io
import requests
from bs4 import BeautifulSoup # 用于解析网页内容

st.set_page_config(page_title="全球原版书智能推荐系统", layout="wide")
st.title("🌐 全球原版书深度推荐系统 (英/日文加强版)")

def get_foreign_book_info(isbn):
    """
    根据ISBN自动判断语种并从对应国家站点抓取信息
    """
    isbn = str(isbn).replace('-', '').strip()
    
    # 简单的语种判断逻辑：4开头通常为日本，0/1开头为英美
    is_japanese = isbn.startswith('9784') or isbn.startswith('4')
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    if is_japanese:
        # 尝试访问日本图书检索接口或公开页面 (此处以常用开放接口为例)
        url = f"https://api.openbd.jp/v1/get?isbn={isbn}"
        try:
            res = requests.get(url, headers=headers, timeout=8)
            data = res.json()
            if data and data[0]:
                summary = data[0]['summary'].get('description', '')
                author_bio = data[0]['onix'].get('CollateralDetail', {}).get('TextContent', [{}])[0].get('Text', '')
                return f"【日文原版解析】: {summary[:100]}... (作者介绍: {author_bio[:50]})"
        except:
            return None
    else:
        # 英文书处理逻辑
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        try:
            res = requests.get(url, headers=headers, timeout=8)
            data = res.json()
            if "items" in data:
                desc = data["items"][0]["volumeInfo"].get("description", "")
                return f"【英文原版解析】: {desc[:100]}..."
        except:
            return None
    return None

def generate_custom_reason(row, audience, style):
    # 联网获取“看一眼”的深度内容
    online_info = get_foreign_book_info(row['ISBN'])
    
    # 风格化文案模板
    templates = {
        "学术": "该著作在国际学术界具有独到视角，其论证严密，是相关研究领域不可多得的参考文献。",
        "大众": "本书叙述生动，即便是不具备专业背景的读者也能从中获得启发，阅读体验极佳。",
        "大学生": "推荐给希望拓展国际视野的同学们，书中的案例和理论对毕业论文或课程设计极具参考价值。",
        "低龄儿童": "图文并茂（或构思精巧），是培养外语语感和跨文化思维的优质启蒙读物。"
    }

    base = templates.get(style, "优秀的海外原版读物。")
    
    if online_info:
        return f"{online_info} \n\n【推荐建议】：{base}"
    else:
        return f"《{row['书名']}》由{row['出版社']}原版引进，著者{row['著者']}在海外享有盛誉。{base}"

# --- 侧边栏 ---
with st.sidebar:
    st.header("⚙️ 跨境推荐配置")
    uploaded_file = st.file_uploader("上传 Excel 目录 (含英文/日文书)", type=["xlsx"])
    num_rec = st.number_input("推荐数量", min_value=1, max_value=20, value=3)
    target_audience = st.selectbox("目标受众", ["图书馆", "普通大众"])
    style_preference = st.selectbox("推荐风格", ["学术", "大众", "大学生", "低龄儿童"])
    st.caption("提示：推荐日文书时，系统会自动调用日本图书数据库接口。")

# --- 主程序 ---
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()
    
    if 'ISBN' in df.columns:
        if st.button("🔍 开始跨国联网分析"):
            actual_num = min(len(df), int(num_rec))
            selected_df = df.sample(n=actual_num).copy()
            
            progress_bar = st.progress(0)
            reasons = []
            
            for i, (idx, row) in enumerate(selected_df.iterrows()):
                st.write(f"正在跨境检索: 《{row['书名']}》...")
                reasons.append(generate_custom_reason(row, target_audience, style_preference))
                progress_bar.progress((i + 1) / actual_num)
            
            selected_df['推荐理由'] = reasons
            st.success("✨ 分析完成！")
            
            st.table(selected_df[['书名', '著者', '出版社', '推荐理由']])
            
            # 导出
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                selected_df.to_excel(writer, index=False)
            st.download_button("📥 下载带深度理由的清单", output.getvalue(), "海外书深度推荐.xlsx")
    else:
        st.error("表格必须包含 ISBN 列！")
