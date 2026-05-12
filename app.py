import streamlit as st
import pandas as pd
import random
import io  # <--- 关键修复：补上了这个导入语句

# 1. 页面基本配置
st.set_page_config(page_title="智能图书推荐系统", layout="wide")
st.title("📚 智能图书推荐管理系统")

# 2. 推荐理由生成函数 (方案 B：逻辑映射)
def generate_smart_reason(row, audience, style):
    # 基础备选库
    reasons_map = {
        "图书馆": {
            "学术": [f"该书由{row['出版社']}出版，学术架构严谨，建议作为专业文献入藏。", "具有极高的学术参考价值，适合高校科研教学使用。"],
            "大学生": ["内容深度适中，是大学生构建专业知识体系的优质读物。", "结合了理论与实践，推荐作为大学通识课辅助教材。"],
            "大众": ["虽为学术背景，但文字通俗，适合公共图书馆提升藏书质量。"],
            "低龄儿童": ["以科普视角切入，适合少儿阅览室作为启蒙读物。"]
        },
        "普通大众": {
            "大众": [f"《{row['书名']}》是近期值得一读的精品，推荐给追求生活质量的读者。", "文笔生动且富有见地，是年度不容错过的‘种草’好书。"],
            "学术": ["适合对该领域有深度钻研兴趣的进阶读者。", "硬核知识科普，适合喜欢挑战思维边界的你。"],
            "大学生": ["职场进阶与学业提升的有力助手，语言精炼。"],
            "低龄儿童": ["色彩与文字配合巧妙，是亲子共读的绝佳选择。", "激发孩子好奇心，开启探索世界的第一步。"]
        }
    }
    
    # 逻辑提取：如果匹配不到，则给出一个通用理由
    try:
        options = reasons_map.get(audience, {}).get(style, [f"本书由{row['著者']}撰写，是{row['出版社']}近期力作。"])
        return random.choice(options)
    except:
        return "推荐理由正在生成中，建议根据书名进一步查阅。"

# 3. 侧边栏交互界面
with st.sidebar:
    st.header("⚙️ 参数配置")
    uploaded_file = st.file_uploader("1. 上传 Excel 新书目录", type=["xlsx"])
    num_rec = st.number_input("2. 推荐数量", min_value=1, max_value=200, value=5)
    target_audience = st.selectbox("3. 目标受众", ["图书馆", "普通大众"])
    style_preference = st.selectbox("4. 推荐风格", ["学术", "大众", "大学生", "低龄儿童"])

# 4. 主程序逻辑
if uploaded_file:
    try:
        # 读取 Excel
        df = pd.read_excel(uploaded_file)
        
        # 清洗列名，防止空格导致系统找不到列
        df.columns = df.columns.str.strip()
        
        required_cols = ['ISBN', '书名', '著者', '出版社', '出版时间', '价格']
        
        # 验证表格格式
        if all(col in df.columns for col in required_cols):
            st.success("✅ 目录解析成功！")
            
            if st.button("🚀 开始生成推荐"):
                # 处理抽样数量，防止数量超过表格总数
                actual_num = min(len(df), int(num_rec))
                selected_df = df.sample(n=actual_num).copy()
                
                # 生成推荐语
                selected_df['推荐理由'] = selected_df.apply(
                    lambda row: generate_smart_reason(row, target_audience, style_preference), 
                    axis=1
                )
                
                # 页面展示
                st.subheader(f"📍 针对【{target_audience}】的【{style_preference}】风清单")
                st.dataframe(selected_df[['书名', '著者', '价格', '推荐理由']], use_container_width=True)
                
                # 5. 导出功能 (之前报错的地方)
                output = io.BytesIO() # 现在程序认识 io 了
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    selected_df.to_excel(writer, index=False, sheet_name='推荐结果')
                
                st.download_button(
                    label="📥 下载生成的推荐清单 (Excel)",
                    data=output.getvalue(),
                    file_name="智能图书推荐表.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.error(f"⚠️ 表格缺少必要列。请检查是否包含: {required_cols}")
            
    except Exception as e:
        st.error(f"❌ 读取文件时发生错误: {e}")
else:
    st.info("💡 请先在左侧上传您的 Excel 目录文件。")
