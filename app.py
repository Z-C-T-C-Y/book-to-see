import streamlit as st
import pandas as pd
import random

# 设置页面配置
st.set_page_config(page_title="智能图书推荐系统", layout="wide")

st.title("📚 智能图书推荐管理系统 (方案 B)")
st.markdown("---")

# 侧边栏：配置参数
with st.sidebar:
    st.header("⚙️ 推荐配置")
    uploaded_file = st.file_uploader("第一步：上传新书目录 (Excel)", type=["xlsx"])
    
    if uploaded_file:
        num_rec = st.number_input("第二步：计划推荐数量", min_value=1, max_value=50, value=5)
        
        target_audience = st.selectbox(
            "第三步：选择目标受众",
            options=["图书馆", "普通大众"]
        )
        
        style_preference = st.selectbox(
            "第四步：选择推荐风格",
            options=["学术", "大众", "大学生", "低龄儿童"]
        )

# 推荐理由生成引擎 (方案 B 核心逻辑)
def generate_smart_reason(row, audience, style):
    # 这里模拟了基于 ISBN/书名的语义化理由生成逻辑
    reasons = {
        "图书馆": {
            "学术": [
                f"该书由{row['出版社']}出版，具有极高的文献收藏价值，建议作为{row['著者']}的研究文献入藏。",
                f"本书在学术界具有广泛影响力，适合补充馆内相关学科的理论深度。"
            ],
            "大学生": [
                f"内容贴合当前高校教学大纲，是图书馆为学生提供课外科研参考的优选书目。",
                f"适合作为大学生通识教育的辅助读物，提升馆藏的实用性和借阅率。"
            ]
        },
        "普通大众": {
            "大众": [
                f"《{row['书名']}》以平实的语言揭示了深刻的道理，是居家旅行或睡前阅读的精品之选。",
                f"如果你正在寻找一本能够开阔眼界的书籍，{row['著者']}的这本新作绝对不容错过。"
            ],
            "低龄儿童": [
                f"色彩丰富、语言生动，非常适合家长与孩子共读，开启孩子的探索之窗。",
                f"针对低幼龄段设计的互动感强，是培养孩子阅读习惯的极佳入门书。"
            ]
        }
    }
    
    # 逻辑容错处理
    try:
        category = reasons.get(audience, {}).get(style, [f"本书《{row['书名']}》内容扎实，推荐购买。"])
        return random.choice(category)
    except:
        return f"这是一本由{row['出版社']}出品的优质图书，推荐阅读。"

# 主界面逻辑
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # 检查列名
    required_cols = ['ISBN', '书名', '著者', '出版社', '出版时间', '价格']
    if all(col in df.columns for col in required_cols):
        st.success("✅ 目录解析成功！")
        
        if st.button("🚀 生成推荐清单"):
            # 随机抽选指定数量
            if len(df) < num_rec:
                num_rec = len(df)
            
            selected_df = df.sample(n=num_rec).copy()
            
            # 生成理由
            selected_df['推荐理由'] = selected_df.apply(
                lambda row: generate_smart_reason(row, target_audience, style_preference), axis=1
            )
            
            # 展示结果
            st.subheader(f"📍 为【{target_audience}】定制的【{style_preference}】风格推荐清单")
            st.table(selected_df[['书名', '著者', '价格', '推荐理由']])
            
            # 提供下载
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                selected_df.to_excel(writer, index=False, sheet_name='推荐清单')
            
            st.download_button(
                label="📥 下载推荐结果 (Excel)",
                data=output.getvalue(),
                file_name="推荐清单_result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.error(f"❌ Excel格式不符，请确保包含以下列：{', '.join(required_cols)}")
else:
    st.info("💡 请在左侧上传 Excel 文件开始操作。")