from fastapi import FastAPI
from contextlib import asynccontextmanager
import database_manager as dm
import data_crawler as dc
from apscheduler.schedulers.background import BackgroundScheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # > 서버 시작 시 DB 초기화
    dm.init_db() 
    
    scheduler = BackgroundScheduler()
    
    # { "섹션명": "검색 키워드" }
    target_sections = {
        "속보": '속보 | 실시간 | "단독"',
        "IT/과학": "IT | 과학 | 테크 | AI | 반도체",
        "정치": "정치 | 국회 | 정당 | 대통령",
        "세계": "세계 | 국제 | 외신 | 해외",
        "경제": "경제 | 증시 | 금융 | 부동산 | 물가"
    }
    
    for section_name, search_keyword in target_sections.items():
        # ★ 핵심 포인트 1: args에 [섹션명, 검색키워드] 2개를 리스트로 묶어 전달해야 함
        scheduler.add_job(
            dc.updateNewsSummary, 
            'interval', 
            hours=3, 
            args=[section_name, search_keyword] # 인자 2개!
        )
        
        # ★ 핵심 포인트 2: 즉시 실행할 때도 인자 2개를 다 넣어야 함
        dc.updateNewsSummary(section_name, search_keyword) # 인자 2개!
    
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/api/news_summary")
def get_all_summary():
    # 간단하게 DB 확인용 API (실제 서비스는 Streamlit 이용)
    return {"status": "success", "message": "Backend is running!"}