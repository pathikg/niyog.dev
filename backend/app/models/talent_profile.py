from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()


class TalentProfile(Base):
    __tablename__ = "talent_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    talent_id = Column(UUID(as_uuid=True), ForeignKey("talent_users.id", ondelete="CASCADE"), nullable=False)
    schema_id = Column(UUID(as_uuid=True), ForeignKey("schemas.id", ondelete="CASCADE"), nullable=False)
    onboarding_session_id = Column(UUID(as_uuid=True), ForeignKey("onboarding_sessions.id", ondelete="SET NULL"), nullable=True)
    data = Column(JSONB, nullable=False, default={})
    is_final = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="talent_profiles")
    talent = relationship("TalentUser", back_populates="talent_profiles")
    schema = relationship("Schema", back_populates="talent_profiles")
    onboarding_session = relationship("OnboardingSession", back_populates="talent_profile")
    files = relationship("File", back_populates="talent_profile")

    # Indexes
    __table_args__ = (
        Index("idx_profiles_talent", "talent_id"),
        Index("idx_profiles_company", "company_id"),
        Index("idx_profiles_schema", "schema_id"),
        Index("idx_profiles_data", "data", postgresql_using="gin"),
    )

    def __repr__(self):
        return f"<TalentProfile(id={self.id}, talent_id={self.talent_id}, is_final={self.is_final})>"
