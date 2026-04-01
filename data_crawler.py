import requests
import json
import google.generativeai as genai
from datetime import datetime
import database_manager as dm
import streamlit as  st

def getTodayNewsData(query):
    # > 뉴스 데이터 추출
    client_id = st.secrets["NAVER_CLIENT_ID"]
    client_secret = st.secrets["NAVER_CLIENT_SECRET"]
    api_url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    params = {
        "query": query, 
        "display": 100, 
        "sort": "date"
    }
    response = requests.get(
        api_url, 
        headers=headers, 
        params=params
    )
    today_str = datetime.now().strftime("%d %b %Y") # API 날짜 형식과 맞춤
    news_list = []
    
    if response.status_code == 200:
        items = response.json().get('items', [])
        for item in items:
            pub_date = item['pubDate'] 
            if today_str in pub_date:
                clean_title = item['title'].replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
                news_list.append({
                    "title": clean_title
                })
    return news_list

def geminiSummary(newsListText, section_name):
    # > 제미나이 요약 함수
    # Date: 26.04.01
    
    # --- 만약 AI를 쓰고 싶다면 아래 주석을 푸세요 ---
    googleApiKey = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key = googleApiKey)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
        아래 뉴스들을 종합해서 가장 중요한 소식 3가지를 요약해줘.
        반드시 아래의 JSON 리스트 형식으로만 응답해. 
        다른 설명은 생략해.
        
        [
          {{"title": "구체적인 소식 제목1", "content": "요약 문장1"}},
          {{"title": "구체적인 소식 제목2", "content": "요약 문장2"}},
          {{"title": "구체적인 소식 제목3", "content": "요약 문장3"}}
        ]
        
        뉴스 내용:
        {newsListText}
    """
    
    try:
        response = model.generate_content(prompt).text
        # JSON 문자열 정제 (백틱이나 줄바꿈 제거)
        jsonResponse = (
            response
                .replace(r"```json", "")
                .replace("\n", "")
                .replace("```", "")
                .replace("  ", "")
                .replace("    ", "")
                .strip()
        )
        return json.loads(jsonResponse)
    
    except Exception as e:
        print(f"❌ Gemini API 에러 혹은 쿼터 초과: {e}")
        # 에러가 나면 여기서 '섹션에 맞는' 가짜 데이터를 리턴!
        return generateMockData(section_name)
    
    # return generateMockData(section_name)

def updateNewsSummary(section_name, search_keyword):
    # > 뉴스 업데이트 작업
    print(f"🚀 [Job] {section_name} 업데이트 시작 (키워드: {search_keyword})")
    try:
        ## News 데이터 처리
        raw_news = getTodayNewsData(search_keyword)
        titles_only = [news['title'] for news in raw_news]
        
        if not titles_only:
            print(f"⚠️ {section_name}에 오늘자 뉴스가 없습니다.")
            return

        summary_data = geminiSummary(titles_only, section_name)
        
        ## Image 처리
        for item in summary_data:
            imageURL = getNaverImages(item["title"])
            item["image"] = imageURL

        dm.insert_data(
            database="news",
            table="summary", 
            category=section_name,
            values=summary_data
        )
        print(f"✅ {section_name} 저장 완료!")
    except Exception as e:
        print(f"> Fail {section_name}: {e}")

def generateMockData(section_name):
    # > 섹션별 맞춤형 목업 데이터 생성
    print(f"⚠️ [Warning] '{section_name}' 섹션 쿼터 초과로 가짜 데이터를 반환합니다.")
    
    mock_db = {
        "속보": [
            {"title": "[속보] 정부, 전국 주요 도로 자율주행 전용 차로 도입 발표", "content": "국토교통부가 2027년 완전 자율주행 상용화를 앞두고 전국 주요 고속도로에 자율주행 전용 차로를 구축하는 계획을 전격 발표했습니다."},
            {"title": "속보: 코스피, 외국인 매수세에 힘입어 6,000선 돌파", "content": "코스피 지수가 반도체 대형주를 중심으로 한 외국인과 기관의 강력한 동반 매수세에 힘입어 연중 최고치를 경신했습니다."},
            {"title": "[단독] 글로벌 빅테크 기업, 한국에 아시아 최대 데이터센터 건립", "content": "글로벌 IT 거물이 한국의 우수한 인프라와 지리적 이점을 활용해 아시아 시장을 겨냥한 초대형 데이터센터 건립을 확정했습니다."}
        ],
        "IT/과학": [
            {"title": "애플, 차세대 'M4 칩' 탑재 아이패드 프로 전격 공개", "content": "애플이 AI 연산 성능을 비약적으로 높인 M4 프로세서를 공개하며, 역대 가장 얇은 두께의 아이패드 프로 라인업을 선보였습니다."},
            {"title": "엔비디아 주가, AI 반도체 수요 폭발에 역대 최고치 경신", "content": "글로벌 빅테크 기업들의 생성형 AI 도입 가속화로 인해 엔비디아의 H100 등 AI 가속기 수요가 공급을 앞지르고 있습니다."},
            {"title": "국내 연구진, 세계 최초 '상온 양자 컴퓨터' 소자 개발", "content": "국내 대학 연구팀이 극저온이 아닌 상온에서도 작동 가능한 양자 비트 제어 기술을 확보해 상용화 시기를 앞당겼습니다."}
        ],
        "정치": [
            {"title": "여야, 내년도 예산안 극적 합의... 민생 경제 회복 주력", "content": "평행선을 달리던 여야가 민생 경제 회복을 최우선 과제로 삼고 내년도 예산안 처리에 극적으로 합의하며 민생 법안 처리에 속도를 내기로 했습니다."},
            {"title": "국무회의 소집, '디지털 플랫폼 정부' 혁신 과제 논의", "content": "정부는 국무회의를 통해 인공지능 기반의 행정 서비스 혁신을 목표로 하는 디지털 플랫폼 정부의 5대 핵심 추진 과제를 점검했습니다."},
            {"title": "주요 당국자, 한미 동맹 강화 및 안보 현안 점검", "content": "한미 양측은 고위급 회담을 통해 글로벌 공급망 재편에 대응하고 포괄적인 전략적 파트너십을 더욱 강화하기로 재확인했습니다."}
        ],
        "경제": [
            {"title": "한국은행, 기준금리 동결 결정... '물가 안정에 총력'", "content": "한국은행 금융통화위원회가 대내외 불확실성을 고려하여 기준금리를 현 수준에서 동결하고, 당분간 물가 안정 기조를 유지하기로 했습니다."},
            {"title": "K-푸드 수출액 역대 최고... 북미·유럽 시장 석권", "content": "한국의 라면, 김 등 K-푸드 수출이 전 세계적인 인기에 힘입어 역대 최대 실적을 기록하며 수출 효자 품목으로 자리매김했습니다."},
            {"title": "국내 신규 스타트업 투자 10조 원 돌파... 벤처 열풍 재현", "content": "벤처 투자 시장이 AI와 바이오 분야를 중심으로 활기를 되찾으며, 올해 신규 투자 규모가 10조 원을 넘어서는 등 제2의 벤처 붐이 일고 있습니다."}
        ],
        "세계": [
            {"title": "미국 증시, 금리 인하 기대감에 '산타 랠리' 현실화", "content": "미국 연준의 금리 인하 신호가 감지되면서 뉴욕 증시의 3대 지수가 일제히 사상 최고치를 향해 질주하고 있습니다."},
            {"title": "EU, 탄소 중립 위한 '에너지 혁신법' 공식 발효", "content": "유럽연합이 기후 위기 대응을 위해 신재생 에너지 전환 속도를 높이는 강력한 에너지 혁신법을 오늘부터 전면 시행합니다."},
            {"title": "글로벌 빅테크 경쟁 격화... 일본 정부 'AI 인프라' 집중 투자", "content": "일본 정부가 인공지능 주도권을 확보하기 위해 글로벌 빅테크 기업들과 협력하여 대규모 AI 전용 인프라 구축에 수조 원을 투입합니다."}
        ]
    }
    
    # 해당 섹션이 없으면 기본값(IT/과학 뉴스) 반환
    return mock_db.get(section_name, mock_db["IT/과학"])

def getNaverImages(query):
    # > 이미지 검색 API
    client_id = st.secrets["NAVER_CLIENT_ID"]
    client_secret = st.secrets["NAVER_CLIENT_SECRET"]
    url = "https://openapi.naver.com/v1/search/image"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    params = {
        "query": query, 
        "display": 1,
        "sort": "date", 
        "filter": "large"
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['items']:
                return data['items'][0]['thumbnail']
    except:
        pass
    return "https://via.placeholder.com/300x200?text=No+Image"