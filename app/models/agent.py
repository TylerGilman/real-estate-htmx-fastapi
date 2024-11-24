from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Brokerage(Base, TimestampMixin):
    __tablename__ = "Brokerage"

    broker_id = Column(Integer, primary_key=True, autoincrement=True)
    broker_name = Column(String(255), nullable=False)
    broker_address = Column(String(255))
    broker_phone = Column(String(15))
    broker_email = Column(String(255))
    broker_license = Column(String(50), unique=True, nullable=False)

    # Relationships
    agents = relationship("Agent", back_populates="brokerage")


class Agent(Base, TimestampMixin):
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

    # Relationships
    brokerage = relationship("Brokerage", back_populates="agents")
    listings = relationship("AgentListing", back_populates="agent")
    showings = relationship("AgentShowing", back_populates="agent")
    contracts = relationship("Contract", back_populates="agent")
    transactions = relationship("Transaction", back_populates="agent")
