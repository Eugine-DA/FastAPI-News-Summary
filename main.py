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
    
    target_sections = {
        "속보": '속보 | 실시간 | "단독"',
        "IT/과학": "IT | 과학 | 테크 | AI | 반도체",
        "정치": "정치 | 국회 | 정당 | 대통령",
        "세계": "세계 | 국제 | 외신 | 해외",
        "경제": "경제 | 증시 | 금융 | 부동산 | 물가"
    }
    
    for section_name, search_keyword in target_sections.items():
        scheduler.add_job(
            dc.updateNewsSummary, 
            'cron',          # 특정 시각에 실행
            hour=9,          
            minute=0,        
            args=[section_name, search_keyword]
        )
        dc.updateNewsSummary(section_name, search_keyword)
    
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/api/news_summary")
def get_all_summary():
    # DB 확인용 API
    return {"status": "success", "message": "Backend is running!"}