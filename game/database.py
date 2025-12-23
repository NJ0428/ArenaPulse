import sqlite3
import os
from .config import DATABASE_PATH


class Database:
    def __init__(self):
        # data 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.cursor = self.conn.cursor()
        self._init_tables()

    def _init_tables(self):
        """기본 테이블 생성"""
        # 플레이어 테이블
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                score INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 게임 설정 테이블
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        self.conn.commit()
        print("[DB] 데이터베이스 초기화 완료")

    def add_player(self, name: str) -> int:
        """새 플레이어 추가"""
        self.cursor.execute(
            "INSERT INTO players (name) VALUES (?)",
            (name,)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_player(self, player_id: int):
        """플레이어 정보 조회"""
        self.cursor.execute(
            "SELECT * FROM players WHERE id = ?",
            (player_id,)
        )
        return self.cursor.fetchone()

    def update_score(self, player_id: int, score: int):
        """플레이어 점수 업데이트"""
        self.cursor.execute(
            "UPDATE players SET score = ? WHERE id = ?",
            (score, player_id)
        )
        self.conn.commit()

    def get_setting(self, key: str, default=None):
        """설정 값 조회"""
        self.cursor.execute(
            "SELECT value FROM settings WHERE key = ?",
            (key,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else default

    def set_setting(self, key: str, value: str):
        """설정 값 저장"""
        self.cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        self.conn.commit()

    def close(self):
        """데이터베이스 연결 종료"""
        self.conn.close()
        print("[DB] 데이터베이스 연결 종료")
