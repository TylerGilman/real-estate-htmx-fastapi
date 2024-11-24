from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.types import DECIMAL
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
from .enums import PropertyStatus

class Property(Base, TimestampMixin):
    __tablename__ = "Property"

    property_id = Column(Integer, primary_key=True, autoincrement=True)
    tax_id = Column(String(50), unique=True, nullable=False)
    property_address = Column(String(255), nullable=False)
    status = Column(Enum(PropertyStatus), nullable=False)
    price = Column(DECIMAL(15, 2), nullable=False)
    lot_size = Column(DECIMAL(10, 2))
    year_built = Column(Integer)
    zoning = Column(String(50))
    property_tax = Column(DECIMAL(10, 2))

    # Relationships
    residential = relationship("ResidentialProperty", back_populates="property", uselist=False)
    commercial = relationship("CommercialProperty", back_populates="property", uselist=False)
    listings = relationship("AgentListing", back_populates="property")
    showings = relationship("AgentShowing", back_populates="property")
    contracts = relationship("Contract", back_populates="property")
    transactions = relationship("Transaction", back_populates="property")

class ResidentialProperty(Base, TimestampMixin):
    __tablename__ = "ResidentialProperty"

    property_id = Column(Integer, ForeignKey("Property.property_id"), primary_key=True)
    bedrooms = Column(Integer)
    bathrooms = Column(DECIMAL(3, 1))
    r_type = Column(String(50))
    square_feet = Column(DECIMAL(10, 2))
    garage_spaces = Column(Integer)
    has_basement = Column(Boolean)
    has_pool = Column(Boolean)

    # Relationships
    property = relationship("Property", back_populates="residential")

class CommercialProperty(Base, TimestampMixin):
    __tablename__ = "CommercialProperty"

    property_id = Column(Integer, ForeignKey("Property.property_id"), primary_key=True)
    sqft = Column(DECIMAL(10, 2))
    industry = Column(String(255))
    c_type = Column(String(50))
    num_units = Column(Integer)
    parking_spaces = Column(Integer)
    zoning_type = Column(String(50))

    # Relationships
    property = relationship("Property", back_populates="commercial")
