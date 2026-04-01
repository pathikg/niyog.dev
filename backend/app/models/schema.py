from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Integer, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Schema(Base):
    __tablename__ = "schemas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(50), nullable=False, default="draft")
    definition = Column(JSONB, nullable=False, default={})
    created_by = Column(UUID(as_uuid=True), ForeignKey("hr_users.id", ondelete="SET NULL"), nullable=True)
    hr_thread_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    # Relationships
    company = relationship("Company", back_populates="schemas")
    created_by_user = relationship("HRUser", back_populates="schemas")
    onboarding_sessions = relationship("OnboardingSession", back_populates="schema", cascade="all, delete-orphan")
    talent_profiles = relationship("TalentProfile", back_populates="schema")

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'active', 'archived')", name="ck_schema_status"),
        UniqueConstraint("company_id", "version", name="uq_schemas_company_version"),
        Index("idx_schemas_company_status", "company_id", "status"),
        Index("idx_schemas_definition", "definition", postgresql_using="gin"),
    )

    def __repr__(self):
        return f"<Schema(id={self.id}, company_id={self.company_id}, version={self.version}, status={self.status})>"
