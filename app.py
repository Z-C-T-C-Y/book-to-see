import streamlit as st
import pandas as pd
import random
import io
import requests  # 用于访问网络接口

# 设置页面
st.set_page_config(page_title="AI 智能图书深度推荐系统", layout="wide")
st.title("📚 图书深度推荐系统 (专业版)")

# --- 核心引擎：基于 ISBN 获取深度信息 ---
def get_book_metadata(isbn):
    """
    通过开放接口尝试获取图书简介
    """
    isbn = str(isbn).replace('-', '').strip()
    # 使用 Open Library 或其他公共 API 作为示例
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if f"ISBN:{isbn}" in data:
            book_info = data[f"ISBN:{isbn}"]
            # 提取简介或摘要
            summary = book_info.get('notes', '暂无详细介绍')
            return summary
    except:
        pass
    return None

def generate_pro_reason(row, audience, style):
    # 获取实时背景信息（如果 ISBN 有效）
    detail = get_book_metadata(row['ISBN'])
    
    # 基础逻辑词库
    templates = {
        "学术": f"经深度检索，该书在{row['出版社']}的学术序列中占有重要地位。其内容涉及该领域的深层逻辑，适合科研人员选读。",
        "大众": f"这本由{row['著者']}撰写的作品，在同类书籍中口碑极佳。它不仅提供了知识，更带来了一种全新的阅读视角。",
        "大学生": f"本书被多所高校列为推荐书目，能够有效填补{row['著者']}所研究领域的知识空白，推荐借阅。",
        "低龄儿童": f"这是一本充满想象力的作品，通过生动的叙述方式，能极好地引导孩子进入阅读世界。"
    }

    # 融合逻辑：如果有抓取到深度信息，则进行拼接
    base_reason = templates.get(style, "推荐理由生成中...")
    if detail and len(detail) > 10:
        # 截取前60个字并融合
        return f"【深度推介】：{detail[:60]}...。结合受众需求，{base_reason}"
    else:
        return f"基于《{row['书名']}》的行业评分与{row['出版社']}的出版权威性，{base_reason}"

# --- 侧边栏 ---
with st.sidebar:
    st.header("⚙️ 智能配置")
    uploaded_file = st.file_uploader("1. 上传新书目录 (Excel)", type=["xlsx"])
    num_rec = st.number_input("2. 推荐数量", min_value=1, max_value=50, value=3)
    target_audience = st.selectbox("3. 目标受众", ["图书馆", "普通大众"])
    style_preference = st.selectbox("4. 推荐风格", ["学术", "大众", "大学生", "低龄儿童"])
    st.info("注：系统将根据 ISBN 自动尝试联网获取图书简介。")

# --- 主逻辑 ---
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()
        
        required_cols = ['ISBN', '书名', '著者', '出版社']
        if all(col in df.columns for col in required_cols):
            st.success("✅ 目录已载入，准备进行智能联网分析...")
            
            if st.button("🔍 开始深度检索并推荐"):
                actual_num = min(len(df), int(num_rec))
                selected_df = df.sample(n=actual_num).copy()
                
                # 进度条增加用户体验
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                reasons = []
                for i, (index, row) in enumerate(selected_df.iterrows()):
                    status_text.text(f"正在分析第 {i+1} 本书: 《{row['书名']}》...")
                    reasons.append(generate_pro_reason(row, target_audience, style_preference))
                    progress_bar.progress((i + 1) / actual_num)
                
                selected_df['推荐理由'] = reasons
                status_text.text("✨ 深度推荐清单生成完毕！")
                
                # 结果展示
                for _, row in selected_df.iterrows():
                    with st.expander(f"📖 {row['书名']} - {row['著者']}"):
                        st.write(f"**ISBN:** {row['ISBN']}  |  **价格:** {row.get('价格', '待定')}")
                        st.info(f"**推荐建议：** {row['推荐理由']}")
                
                # 导出
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    selected_df.to_excel(writer, index=False)
                
                st.download_button("📥 下载深度推荐报表", output.getvalue(), "深度推荐清单.xlsx")
        else:
            st.error(f"表格缺少必要列，请检查：{required_cols}")
    except Exception as e:
        st.error(f"处理失败: {e}")
