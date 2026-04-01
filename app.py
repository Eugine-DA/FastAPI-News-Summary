import streamlit as st
import json
from datetime import datetime, timedelta
import database_manager as dm
import data_crawler as dc

# 1. 페이지 설정
st.set_page_config(page_title="AI 뉴스 대시보드", layout="wide")

# 2. 디자인 CSS
st.markdown("""
    <style>
    .main { background-color: #1E1E1E; }
    h1, h2, h3, p { color: white !important; }
    img { border-radius: 10px; max-height: 150px; object-fit: cover; }
    </style>
    """, unsafe_allow_html=True)

# --- 사이드바 ---
# --- 사이드바 ---
with st.sidebar:
    # 1. 오늘 날짜 표시
    current_date = datetime.now().strftime("%Y.%m.%d")
    st.title(current_date)
    
    # 2. 데이터 먼저 호출 (시간을 미리 알아내기 위해)
    option = st.selectbox(
        '뉴스 섹션을 선택해주세요 👇', # 라벨을 위로 올리거나 아래처럼 처리
        ('속보', 'IT/과학', '정치', '경제', '세계'),
        label_visibility="visible", # 라벨을 보이게 하면 더 직관적입니다
        key="section_select"
    )
    
    row = dm.get_db_data(option)
    
    # 3. 업데이트 시간 계산
    if not row:
        with st.spinner(f"'{option}' 섹션의 첫 데이터를 수집 중입니다... (약 10초 소요)"):
            # 검색 키워드 매핑 (main.py에 있던 걸 가져오거나 간단히 처리)
            keywords = {
                "속보": '속보 | 실시간', "IT/과학": "IT | 테크", 
                "정치": "정치", "경제": "경제", "세계": "세계"
            }
            dc.updateNewsSummary(option, keywords.get(option, option))
            row = dm.get_db_data(option) # 다시 가져오기    
    if row:
        try:
            db_time = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
            display_time = (db_time + timedelta(hours=9)).strftime("%H:%M")
        except:
            display_time = row[1][11:16]
    else:
        display_time = "00:00"
    
    # 4. 날짜 바로 아래에 업데이트 시간 배치 (원하셨던 위치!)
    st.caption(f"Last updated at {display_time}")
    
    st.write("---")
    # 섹션 선택기 위치를 옮기고 싶다면 위 st.selectbox 위치를 여기서 조절하면 됩니다.

# --- 메인 영역 ---
st.header(f"오늘의 {option} 핵심 요약")

if row:
    news_list = json.loads(row[0])
    for item in news_list:
        col1, col2 = st.columns([8, 2])
        with col1:
            st.subheader(item['title'])
            st.write(item['content'])
        with col2:
            st.image(item.get('image', "https://via.placeholder.com/150"))
        st.write("---")
else:
    st.info(f"'{option}' 섹션의 데이터를 수집 중입니다. 잠시만 기다려주세요!")