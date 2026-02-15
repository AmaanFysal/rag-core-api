from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.base import Base

class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    content_hash: Mapped[str|None] = mapped_column(String(64), nullable=True, index=True)
    storage_path: Mapped[str|None] = mapped_column(String(1024), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    owner_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")