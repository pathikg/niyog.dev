from sqlalchemy import Column, String, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()


class TalentUser(Base):
    __tablename__ = "talent_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    api_token = Column(String(255), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="talent_users")
    onboarding_sessions = relationship("OnboardingSession", back_populates="talent", cascade="all, delete-orphan")
    talent_profiles = relationship("TalentProfile", back_populates="talent", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint("company_id", "email", name="uq_talent_users_company_email"),
        Index("idx_talent_users_company", "company_id"),
    )

    def __repr__(self):
        return f"<TalentUser(id={self.id}, email={self.email}, company_id={self.company_id})>"
