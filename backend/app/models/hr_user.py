from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()


class HRUser(Base):
    __tablename__ = "hr_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    api_token = Column(String(255), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="hr_users")
    schemas = relationship("Schema", back_populates="created_by_user")

    # Indexes
    __table_args__ = (
        Index("idx_hr_users_company", "company_id"),
    )

    def __repr__(self):
        return f"<HRUser(id={self.id}, email={self.email}, company_id={self.company_id})>"
