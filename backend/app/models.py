from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name_es = Column(String, nullable=False)
    name_en = Column(String)
    name_ca = Column(String)
    cat = Column(String, nullable=False)
    origin = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    ns = Column(String)           # Nutriscore A-E
    es_score = Column(String)     # Ecoscore A-E
    emoji = Column(String)
    season = Column(String)
    year_round = Column(Boolean, default=True)
    co2 = Column(Float)
    desc_es = Column(Text)
    desc_en = Column(Text)
    desc_ca = Column(Text)
    off_barcode = Column(String, index=True)   # Open Food Facts barcode (optional)
    off_updated_at = Column(DateTime)          # Last sync timestamp from OFF

    certs = relationship(
        "ProductCert", back_populates="product", cascade="all, delete-orphan"
    )
    benefits = relationship(
        "ProductBenefit",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductBenefit.position",
    )


class ProductCert(Base):
    __tablename__ = "product_certs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    lang = Column(String, nullable=False)   # 'es' | 'en' | 'ca'
    cert = Column(String, nullable=False)

    product = relationship("Product", back_populates="certs")


class ProductBenefit(Base):
    __tablename__ = "product_benefits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    lang = Column(String, nullable=False)
    benefit = Column(String, nullable=False)
    position = Column(Integer, default=0)

    product = relationship("Product", back_populates="benefits")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    action = Column(String, nullable=False)   # 'click' | 'search' | 'chat'
    query = Column(String)
    lang = Column(String)
    user_lat = Column(Float)
    user_lon = Column(Float)
    ts = Column(DateTime(timezone=True), server_default=func.now())
