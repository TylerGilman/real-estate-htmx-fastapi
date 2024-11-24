from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, Enum, Boolean
from sqlalchemy.types import DECIMAL
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
from .enums import AgentRole, ContractType, TransactionType

class AgentListing(Base, TimestampMixin):
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

    # Relationships
    property = relationship("Property", back_populates="listings")
    agent = relationship("Agent", back_populates="listings")
    client = relationship("Client", back_populates="listings")

class AgentShowing(Base, TimestampMixin):
    __tablename__ = "AgentShowing"

    showing_id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Integer, ForeignKey("Property.property_id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("Agent.agent_id"), nullable=False)
    client_id = Column(Integer, ForeignKey("Client.client_id"), nullable=False)
    agent_role = Column(Enum(AgentRole), nullable=False)
    showing_date = Column(Date, nullable=False)
    feedback = Column(Text)

    # Relationships
    property = relationship("Property", back_populates="showings")
    agent = relationship("Agent", back_populates="showings")
    client = relationship("Client", back_populates="showings")

class Contract(Base, TimestampMixin):
    __tablename__ = "Contract"

    contract_id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(Integer, ForeignKey("Property.property_id"), nullable=False)
    client_id = Column(Integer, ForeignKey("Client.client_id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("Agent.agent_id"), nullable=False)
    contract_type = Column(Enum(ContractType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    terms = Column(Text)

    # Relationships
    property = relationship("Property", back_populates="contracts")
    client = relationship("Client", back_populates="contracts")
    agent = relationship("Agent", back_populates="contracts")

class Transaction(Base, TimestampMixin):
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

    # Relationships
    property = relationship("Property", back_populates="transactions")
    seller = relationship("Client", foreign_keys=[seller_id], back_populates="sales")
    buyer = relationship("Client", foreign_keys=[buyer_id], back_populates="purchases")
    agent = relationship("Agent", back_populates="transactions")
