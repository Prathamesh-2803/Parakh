"""SQLAlchemy database models for structured BIS data."""

from datetime import datetime

from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Standard(Base):
    """Indian Standards (IS) catalog."""

    __tablename__ = "standards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    standard_no: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    ics_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, withdrawn, revised
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Scheme(Base):
    """BIS certification schemes (ISI, CRS, FMCS, Hallmarking, etc.)."""

    __tablename__ = "schemes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scheme_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    scheme_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProductCategory(Base):
    """Products and their applicable standards/schemes."""

    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    applicable_standard: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scheme_code: Mapped[str | None] = mapped_column(String(50), ForeignKey("schemes.scheme_code"), nullable=True)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    qco_order: Mapped[str | None] = mapped_column(String(100), nullable=True)  # QCO/CRO order no
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)  # DEMO DATA marker

    scheme: Mapped["Scheme"] = relationship("Scheme", foreign_keys=[scheme_code])


class Lab(Base):
    """Recognized testing laboratories."""

    __tablename__ = "labs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lab_name: Mapped[str] = mapped_column(String(300), nullable=False)
    lab_code: Mapped[str | None] = mapped_column(String(50), unique=True, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    accreditation_scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class HallmarkingCentre(Base):
    """Assaying & Hallmarking Centres (AHC)."""

    __tablename__ = "hallmarking_centres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    centre_name: Mapped[str] = mapped_column(String(300), nullable=False)
    centre_code: Mapped[str | None] = mapped_column(String(50), unique=True, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class Fee(Base):
    """Certification and licensing fees."""

    __tablename__ = "fees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scheme_code: Mapped[str] = mapped_column(String(50), ForeignKey("schemes.scheme_code"), nullable=False)
    fee_type: Mapped[str] = mapped_column(String(100), nullable=False)  # application, renewal, inspection
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    scheme: Mapped["Scheme"] = relationship("Scheme", foreign_keys=[scheme_code])


class Feedback(Base):
    """User feedback on chat/recommend responses."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[str] = mapped_column(String(20), nullable=False)  # 'positive' or 'negative'
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MaterialCode(Base):
    """Material codes for plastic resin, gold/silver hallmark, metal grades."""

    __tablename__ = "material_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    material_name: Mapped[str] = mapped_column(String(200), nullable=False)
    common_uses: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    applicable_standards: Mapped[str | None] = mapped_column(Text, default="[]")
    needs_research: Mapped[bool] = mapped_column(Boolean, default=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


