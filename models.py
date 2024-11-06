# models.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    Boolean,
    DateTime,
    Enum,
    Table,
    and_,
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

Base = declarative_base()


# Enums
class PropertyType(enum.Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"


class AgentRole(enum.Enum):
    BUYER = "buyer"
    SELLER = "seller"
    LESSEE = "lessee"


class ClientType(enum.Enum):
    BUYER = "buyer"
    SELLER = "seller"
    LESSEE = "lessee"


# Association Tables
property_client_association = Table(
    "property_client_association",
    Base.metadata,
    Column("tax_id", String, nullable=False),
    Column("property_address", String, nullable=False),
    Column("client_ssn", String, ForeignKey("clients.ssn"), nullable=False),
    ForeignKeyConstraint(
        ["tax_id", "property_address"],
        ["properties.tax_id", "properties.property_address"],
    ),
    PrimaryKeyConstraint("tax_id", "property_address", "client_ssn"),
)


# Core Models
class Property(Base):
    __tablename__ = "properties"

    tax_id = Column(String, primary_key=True)
    property_address = Column(String, primary_key=True)
    status = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    image_url = Column(String)
    image_width = Column(Integer)
    image_height = Column(Integer)
    property_type = Column(Enum(PropertyType), nullable=False)

    # Relationships
    residential_details = relationship(
        "ResidentialProperty",
        back_populates="property",
        uselist=False,
        foreign_keys="[ResidentialProperty.tax_id, ResidentialProperty.property_address]",
    )
    commercial_details = relationship(
        "CommercialProperty",
        back_populates="property",
        uselist=False,
        foreign_keys="[CommercialProperty.tax_id, CommercialProperty.property_address]",
    )
    listings = relationship("AgentListing", back_populates="property")
    showings = relationship("AgentShowing", back_populates="property")
    clients = relationship(
        "Client", secondary=property_client_association, back_populates="properties"
    )


class Brokerage(Base):
    __tablename__ = "brokerages"

    broker_id = Column(Integer, primary_key=True, autoincrement=True)
    broker_name = Column(String, nullable=False)
    broker_address = Column(String, nullable=False)
    broker_phone = Column(String, nullable=False)

    # Relationship with agents
    agents = relationship("Agent", back_populates="brokerage")


class Agent(Base):
    __tablename__ = "agents"

    agent_name = Column(String, primary_key=True)
    agent_phone = Column(String, primary_key=True)
    ssn = Column(String, unique=True)  # Keep SSN as unique but not primary key
    nrds = Column(String, unique=True)  # Keep NRDS as unique but not primary key
    broker_id = Column(Integer, ForeignKey("brokerages.broker_id"), nullable=False)

    # Relationships
    brokerage = relationship("Brokerage", back_populates="agents")
    listings = relationship("AgentListing", back_populates="agent")
    showings = relationship("AgentShowing", back_populates="agent")

class AgentListing(Base):
    __tablename__ = "agent_listings"

    listing_id = Column(Integer, primary_key=True)
    tax_id = Column(String, nullable=False)
    property_address = Column(String, nullable=False)
    agent_name = Column(String, nullable=False)
    agent_phone = Column(String, nullable=False)
    client_phone = Column(String, ForeignKey("clients.client_phone"), nullable=False)
    l_agent_role = Column(Enum(AgentRole), nullable=False)
    listing_date = Column(DateTime, default=datetime.utcnow)
    exclusive = Column(Boolean, default=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ['tax_id', 'property_address'],
            ['properties.tax_id', 'properties.property_address'],
        ),
        ForeignKeyConstraint(
            ['agent_name', 'agent_phone'],
            ['agents.agent_name', 'agents.agent_phone'],
        ),
    )

    property = relationship("Property", back_populates="listings")
    agent = relationship("Agent", back_populates="listings")
    client = relationship("Client", back_populates="listings")

class AgentShowing(Base):
    __tablename__ = "agent_showings"

    showing_id = Column(Integer, primary_key=True)
    tax_id = Column(String, nullable=False)
    property_address = Column(String, nullable=False)
    agent_name = Column(String, nullable=False)
    agent_phone = Column(String, nullable=False)
    client_phone = Column(String, ForeignKey("clients.client_phone"), nullable=False)
    s_agent_role = Column(Enum(AgentRole), nullable=False)
    showing_date = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        ForeignKeyConstraint(
            ['tax_id', 'property_address'],
            ['properties.tax_id', 'properties.property_address'],
        ),
        ForeignKeyConstraint(
            ['agent_name', 'agent_phone'],
            ['agents.agent_name', 'agents.agent_phone'],
        ),
    )

    property = relationship("Property", back_populates="showings")
    agent = relationship("Agent", back_populates="showings")
    client = relationship("Client", back_populates="showings")


# Property Type Models
class ResidentialProperty(Base):
    __tablename__ = "residential_properties"

    tax_id = Column(String, primary_key=True)
    property_address = Column(String, primary_key=True)
    bedrooms = Column(Integer, nullable=False)
    bathrooms = Column(Float, nullable=False)
    r_type = Column(String, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tax_id", "property_address"],
            ["properties.tax_id", "properties.property_address"],
        ),
    )

    # Relationships
    property = relationship(
        "Property",
        back_populates="residential_details",
        foreign_keys=[tax_id, property_address],
    )


class CommercialProperty(Base):
    __tablename__ = "commercial_properties"

    tax_id = Column(String, primary_key=True)
    property_address = Column(String, primary_key=True)
    sqft = Column(Float, nullable=False)
    industry = Column(String, nullable=False)
    c_type = Column(String, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tax_id", "property_address"],
            ["properties.tax_id", "properties.property_address"],
        ),
    )

    # Relationships
    property = relationship(
        "Property",
        back_populates="commercial_details",
        foreign_keys=[tax_id, property_address],
    )


class Client(Base):
    __tablename__ = "clients"

    client_phone = Column(String, primary_key=True)
    client_name = Column(String, nullable=False)
    mailing_address = Column(String, nullable=False)
    ssn = Column(String, unique=True, nullable=True)
    client_type = Column(Enum(ClientType), nullable=False)

    # Relationships
    properties = relationship(
        "Property", 
        secondary=property_client_association, 
        back_populates="clients"
    )
    showings = relationship("AgentShowing", back_populates="client")
    listings = relationship("AgentListing", back_populates="client")


