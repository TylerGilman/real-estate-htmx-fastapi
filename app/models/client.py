from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
from .enums import ClientRole


class Client(Base, TimestampMixin):
    __tablename__ = "Client"

    client_id = Column(Integer, primary_key=True, autoincrement=True)
    client_name = Column(String(255), nullable=False)
    SSN = Column(String(15), unique=True, nullable=False)
    mailing_address = Column(String(255))
    client_phone = Column(String(15))
    client_email = Column(String(255))

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


class ClientRoles(Base, TimestampMixin):
    __tablename__ = "ClientRoles"

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("Client.client_id"), nullable=False)
    role = Column(Enum(ClientRole), nullable=False)

    # Relationships
    client = relationship("Client", back_populates="roles")
