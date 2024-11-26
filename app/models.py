from sqlalchemy import (
    Column,
    Integer,
    String,
    DECIMAL,
    Date,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Enum,
    func,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime

Base = declarative_base()


# Enum Classes
class PropertyStatus(str, enum.Enum):
    FOR_SALE = "For Sale"
    FOR_LEASE = "For Lease"
    SOLD = "Sold"
    LEASED = "Leased"


class ClientRole(str, enum.Enum):
    BUYER = "Buyer"
    SELLER = "Seller"
    LESSEE = "Lessee"


class AgentRole(str, enum.Enum):
    SELLER_AGENT = "SellerAgent"
    BUYER_AGENT = "BuyerAgent"
    LESSEE_AGENT = "LesseeAgent"


class ContractType(str, enum.Enum):
    LISTING = "Listing"
    SHOWING = "Showing"


class TransactionType(str, enum.Enum):
    SALE = "Sale"
    LEASE = "Lease"


# Models
class Brokerage(Base):
    __tablename__ = "Brokerage"

    broker_id = Column(Integer, primary_key=True, autoincrement=True)
    broker_name = Column(String(255), nullable=False)
    broker_address = Column(String(255))
    broker_phone = Column(String(15))
    broker_email = Column(String(255))
    broker_license = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    agents = relationship("Agent", back_populates="brokerage")


class Agent(Base):
    __tablename__ = "Agent"

    agent_id = Column(Integer, primary_key=True, autoincrement=True)
    NRDS = Column(String(50), unique=True, nullable=False)
    agent_name = Column(String(255), nullable=False)
    agent_phone = Column(String(15))
    agent_email = Column(String(255), unique=True)
    SSN = Column(String(15), unique=True, nullable=False)
    broker_id = Column(Integer, ForeignKey("Brokerage.broker_id"))
    license_number = Column(String(50), unique=True, nullable=False)
    license_expiration = Column(Date)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    brokerage = relationship("Brokerage", back_populates="agents")
    listings = relationship("AgentListing", back_populates="agent")
    showings = relationship("AgentShowing", back_populates="agent")
    contracts = relationship("Contract", back_populates="agent")
    transactions = relationship("Transaction", back_populates="agent")


class Client(Base):
    __tablename__ = "Client"

    client_id = Column(Integer, primary_key=True, autoincrement=True)
    client_name = Column(String(255), nullable=False)
    SSN = Column(String(15), unique=True, nullable=False)
    mailing_address = Column(String(255))
    client_phone = Column(String(15))
    client_email = Column(String(255))
    created_at = Column(DateTime, default=func.now())

    # Relationships
    roles = relationship("ClientRoles", back_populates="client")
    listings = relationship("AgentListing", back_populates="client")
    showings = relationship("AgentShowing", back_populates="client")
    contracts = relationship("Contract", back_populates="client")
    sales = relationship(
        "Transaction", foreign_keys="[Transaction.seller_id]", back_populates="seller"
    )
    purchases = relationship(
        "Transaction", foreign_keys="[Transaction.buyer_id]", back_populates="buyer"
    )


class ClientRoles(Base):
    __tablename__ = "ClientRoles"

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("Client.client_id"), nullable=False)
    role = Column(Enum(ClientRole), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    client = relationship("Client", back_populates="roles")


class Property(Base):
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
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    image_url = Column(String(255))

    # Relationships
    residential = relationship(
        "ResidentialProperty", back_populates="property", uselist=False
    )
    commercial = relationship(
        "CommercialProperty", back_populates="property", uselist=False
    )
    listings = relationship("AgentListing", back_populates="property")
    showings = relationship("AgentShowing", back_populates="property")
    contracts = relationship("Contract", back_populates="property")
    transactions = relationship("Transaction", back_populates="property")


class ResidentialProperty(Base):
    __tablename__ = "ResidentialProperty"

    property_id = Column(Integer, ForeignKey("Property.property_id"), primary_key=True)
    bedrooms = Column(Integer)
    bathrooms = Column(DECIMAL(3, 1))
    r_type = Column(String(50))
    square_feet = Column(DECIMAL(10, 2))
    garage_spaces = Column(Integer)
    has_basement = Column(Boolean)
    has_pool = Column(Boolean)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    property = relationship("Property", back_populates="residential")


class CommercialProperty(Base):
    __tablename__ = "CommercialProperty"

    property_id = Column(Integer, ForeignKey("Property.property_id"), primary_key=True)
    sqft = Column(DECIMAL(10, 2))
    industry = Column(String(255))
    c_type = Column(String(50))
    num_units = Column(Integer)
    parking_spaces = Column(Integer)
    zoning_type = Column(String(50))
    created_at = Column(DateTime, default=func.now())

    # Relationships
    property = relationship("Property", back_populates="commercial")


class AgentListing(Base):
    __tablename__ = "AgentListing"

    listing_id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Integer, ForeignKey("Property.property_id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("Agent.agent_id"), nullable=False)
    client_id = Column(Integer, ForeignKey("Client.client_id"), nullable=False)
    agent_role = Column(Enum(AgentRole), nullable=False)
    listing_date = Column(Date, nullable=False)
    expiration_date = Column(Date)
    exclusive = Column(Boolean, nullable=False)
    asking_price = Column(DECIMAL(15, 2), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    property = relationship("Property", back_populates="listings")
    agent = relationship("Agent", back_populates="listings")
    client = relationship("Client", back_populates="listings")


class AgentShowing(Base):
    __tablename__ = "AgentShowing"

    showing_id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Integer, ForeignKey("Property.property_id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("Agent.agent_id"), nullable=False)
    client_id = Column(Integer, ForeignKey("Client.client_id"), nullable=False)
    agent_role = Column(Enum(AgentRole), nullable=False)
    showing_date = Column(Date, nullable=False)
    feedback = Column(Text)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    property = relationship("Property", back_populates="showings")
    agent = relationship("Agent", back_populates="showings")
    client = relationship("Client", back_populates="showings")


class Contract(Base):
    __tablename__ = "Contract"

    contract_id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Integer, ForeignKey("Property.property_id"), nullable=False)
    client_id = Column(Integer, ForeignKey("Client.client_id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("Agent.agent_id"), nullable=False)
    contract_type = Column(Enum(ContractType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    terms = Column(Text)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    property = relationship("Property", back_populates="contracts")
    client = relationship("Client", back_populates="contracts")
    agent = relationship("Agent", back_populates="contracts")


class Transaction(Base):
    __tablename__ = "Transaction"

    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Integer, ForeignKey("Property.property_id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("Client.client_id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("Client.client_id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("Agent.agent_id"), nullable=False)
    transaction_date = Column(Date, nullable=False)
    amount = Column(DECIMAL(15, 2), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    commission_amount = Column(DECIMAL(15, 2))
    closing_date = Column(Date)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    property = relationship("Property", back_populates="transactions")
    seller = relationship("Client", foreign_keys=[seller_id], back_populates="sales")
    buyer = relationship("Client", foreign_keys=[buyer_id], back_populates="purchases")
    agent = relationship("Agent", back_populates="transactions")
