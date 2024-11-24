import enum


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
