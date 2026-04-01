import sqlite3
import json

def init_db():
    # > DB 테이블 생성 (category 컬럼 추가)
    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT, 
            content TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def insert_data(database, table, category, values):
    try:
        conn = sqlite3.connect(f"{database}.db")
        cursor = conn.cursor() 
        # 같은 카테고리의 기존 데이터만 지우고 새로 저장
        cursor.execute(f"DELETE FROM {table} WHERE category = ?", (category,))
        cursor.execute(
            f"INSERT INTO {table} (category, content) VALUES (?, ?)", 
            (category, json.dumps(values, ensure_ascii=False))
        )
        conn.commit()
        conn.close()
        print(f"> Complete DB save: {category}")
    except Exception as e:
        print(f"> DB Insert error: {e}")

def get_db_data(category):
    # > 데이터 호출 전, 테이블이 있는지 한 번 더 확인 (클라우드용 안전장치)
    init_db() 
    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT content, updated_at FROM summary WHERE category = ? ORDER BY id DESC LIMIT 1", (category,))
        row = cursor.fetchone()
    except sqlite3.OperationalError:
        row = None
    conn.close()
    return row