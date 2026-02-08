import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# 資料庫設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "platform.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- 模型定義 (Schema) ---

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    wallet_address = Column(String, unique=True)
    staked_amount = Column(Float, default=0.0) # 質押金
    reputation_score = Column(Integer, default=100) # 信譽分
    is_active = Column(Integer, default=1) # 1=Active, 0=Slashed/Banned

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    budget = Column(Float)
    status = Column(String, default="OPEN") # OPEN, IN_PROGRESS, REVIEW, COMPLETED, DISPUTED
    client_id = Column(String) # 模擬客戶 ID
    assigned_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    result_file_path = Column(String, nullable=True) # 交付檔案路徑 (清洗後)

# 初始化資料庫
def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
