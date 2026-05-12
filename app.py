import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

# --- 增强型尼尔森抓取引擎 ---
def get_nielsen_details_v2(isbn, username, password):
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.nielsenbookdataonline.com/bdol/index.jsp"
    }

    try:
        # 第一步：访问首页获取初始 Cookies 和 Token
        landing = session.get("https://www.nielsenbookdataonline.com/bdol/index.jsp", headers=headers)
        
        # 第二步：登录
        login_url = "https://www.nielsenbookdataonline.com/bdol/auth/login.do"
        login_data = {'username': username, 'password': password}
        session.post(login_url, data=login_data, headers=headers)

        # 第三步：先访问快速查找页面，抓取动态 TOKEN
        search_page = session.get("https://www.nielsenbookdataonline.com/bdol/auth/booksearchadvanced.do", headers=headers)
        token_match = re.search(r'name="org\.apache\.struts\.taglib\.html\.TOKEN" value="([^"]+)"', search_page.text)
        token = token_match.group(1) if token_match else ""

        # 第四步：携带 TOKEN 发起 ISBN 搜索
        # 处理 ISBN，确保没有空格和连字符
        clean_isbn = re.sub(r'[^0-9X]', '', str(isbn))
        find_url = "https://www.nielsenbookdataonline.com/bdol/auth/quickfind.do"
        search_payload = {
            "org.apache.struts.taglib.html.TOKEN": token,
            "quicksearch": clean_isbn
        }
        
        res = session.post(find_url, data=search_payload, headers=headers)
        
        # 第五步：解析复杂的嵌套表格
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 尼尔森的简介通常在 class="details1" 或 "main_text" 的后续表格中
            # 方案：直接查找包含 Description 的加粗文本
            for b_tag in soup.find_all(['strong', 'b', 'th']):
                if "Description" in b_tag.get_text():
                    # 简介通常在同一个单元格或下一个单元格
                    parent_td = b_tag.find_parent('td')
                    if parent_td:
                        full_text = parent_td.get_text(separator=" ", strip=True)
                        # 截取 Description 之后的内容
                        content = full_text.split("Description")[-1].strip()
                        if len(content) > 20: return content
            
            # 保底方案：抓取整个 main_text 区域并清洗
            main_div = soup.find(id="body_main") or soup.find(class_="main_text")
            if main_div:
                text = main_div.get_text(strip=True)
                # 排除 ISBN 和出版日期等杂讯
                if "Hardback" in text:
                    text = text.split("Hardback")[-1]
                return text[:500] # 返回前500字

    except Exception as e:
        return f"抓取异常: {str(e)}"
    return "未在尼尔森找到简介"
