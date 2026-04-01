from sqlalchemy import Column, String, DateTime, ForeignKey, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()


class OnboardingSession(Base):
    __tablename__ = "onboarding_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    talent_id = Column(UUID(as_uuid=True), ForeignKey("talent_users.id", ondelete="CASCADE"), nullable=False)
    schema_id = Column(UUID(as_uuid=True), ForeignKey("schemas.id", ondelete="CASCADE"), nullable=False)
    thread_id = Column(String(255), nullable=False, unique=True)
    status = Column(String(50), nullable=False, default="in_progress")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    company = relationship("Company", back_populates="onboarding_sessions")
    talent = relationship("TalentUser", back_populates="onboarding_sessions")
    schema = relationship("Schema", back_populates="onboarding_sessions")
    talent_profile = relationship("TalentProfile", back_populates="onboarding_session", uselist=False)

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("status IN ('in_progress', 'completed', 'abandoned')", name="ck_session_status"),
        Index("idx_sessions_talent", "talent_id"),
        Index("idx_sessions_company", "company_id"),
    )

    def __repr__(self):
        return f"<OnboardingSession(id={self.id}, talent_id={self.talent_id}, status={self.status})>"
