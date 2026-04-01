from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    hr_users = relationship("HRUser", back_populates="company", cascade="all, delete-orphan")
    talent_users = relationship("TalentUser", back_populates="company", cascade="all, delete-orphan")
    schemas = relationship("Schema", back_populates="company", cascade="all, delete-orphan")
    onboarding_sessions = relationship("OnboardingSession", back_populates="company", cascade="all, delete-orphan")
    talent_profiles = relationship("TalentProfile", back_populates="company", cascade="all, delete-orphan")
    files = relationship("File", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company(id={self.id}, name={self.name}, slug={self.slug})>"
