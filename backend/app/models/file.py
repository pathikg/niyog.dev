from sqlalchemy import Column, String, DateTime, ForeignKey, BigInteger, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()


class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), nullable=False)
    uploader_type = Column(String(50), nullable=False)  # 'talent' or 'hr'
    storage_bucket = Column(String(255), nullable=False)
    storage_key = Column(String(500), nullable=False)
    original_name = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(BigInteger, nullable=True)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="SET NULL"), nullable=True)
    field_key = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="files")
    talent_profile = relationship("TalentProfile", back_populates="files")

    # Indexes
    __table_args__ = (
        Index("idx_files_uploader", "uploaded_by", "uploader_type"),
        Index("idx_files_profile", "profile_id"),
    )

    def __repr__(self):
        return f"<File(id={self.id}, original_name={self.original_name}, storage_key={self.storage_key})>"
