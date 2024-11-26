SET FOREIGN_KEY_CHECKS=0;

CREATE TABLE UserRole (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE User (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    agent_id INT NULL,  -- NULL for admins, populated for agents
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES UserRole(role_id),
    FOREIGN KEY (agent_id) REFERENCES Agent(agent_id) ON DELETE CASCADE
);

-- Insert initial roles
INSERT INTO UserRole (role_name) VALUES ('admin'), ('agent');

-- Brokerage Table
DROP TABLE IF EXISTS Brokerage;
CREATE TABLE Brokerage (
    broker_id INT PRIMARY KEY AUTO_INCREMENT,
    broker_name VARCHAR(255) NOT NULL,
    broker_address VARCHAR(255),
    broker_phone VARCHAR(15),
    broker_email VARCHAR(255),
    broker_license VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent Table
DROP TABLE IF EXISTS Agent;
CREATE TABLE Agent (
    agent_id INT PRIMARY KEY AUTO_INCREMENT,
    NRDS VARCHAR(50) UNIQUE NOT NULL,  -- National REALTOR Database System ID
    agent_name VARCHAR(255) NOT NULL,
    agent_phone VARCHAR(15),
    agent_email VARCHAR(255) UNIQUE,
    SSN VARCHAR(15) UNIQUE NOT NULL,
    broker_id INT,
    license_number VARCHAR(50) UNIQUE NOT NULL,
    license_expiration DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (broker_id) REFERENCES Brokerage(broker_id),
    INDEX idx_agent_name (agent_name)
);

-- Client Table
DROP TABLE IF EXISTS Client;
CREATE TABLE Client (
    client_id INT PRIMARY KEY AUTO_INCREMENT,
    client_name VARCHAR(255) NOT NULL,
    SSN VARCHAR(15) UNIQUE NOT NULL,
    mailing_address VARCHAR(255),
    client_phone VARCHAR(15),
    client_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Client Roles Table
DROP TABLE IF EXISTS ClientRoles;
CREATE TABLE ClientRoles (
    role_id INT PRIMARY KEY AUTO_INCREMENT,
    client_id INT NOT NULL,
    role ENUM ('Buyer', 'Seller', 'Lessee') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES Client(client_id)
);

-- Property Table
DROP TABLE IF EXISTS Property;
CREATE TABLE Property (
    property_id INT PRIMARY KEY AUTO_INCREMENT,
    tax_id VARCHAR(50) UNIQUE NOT NULL,
    property_address VARCHAR(255) NOT NULL,
    status ENUM ('For Sale', 'For Lease', 'Sold', 'Leased') NOT NULL,
    price DECIMAL(15, 2) NOT NULL,
    lot_size DECIMAL(10, 2),  -- in square feet
    year_built INT,
    zoning VARCHAR(50),
    property_tax DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_price (price),
    INDEX idx_address (property_address)
);

-- Residential Property Table
DROP TABLE IF EXISTS ResidentialProperty;
CREATE TABLE ResidentialProperty (
    property_id INT PRIMARY KEY,
    bedrooms INT,
    bathrooms DECIMAL(3, 1),
    r_type VARCHAR(50),  -- Single Family, Condo, Townhouse, etc.
    square_feet DECIMAL(10, 2),
    garage_spaces INT,
    has_basement BOOLEAN,
    has_pool BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES Property(property_id) ON DELETE CASCADE
);

-- Commercial Property Table
DROP TABLE IF EXISTS CommercialProperty;
CREATE TABLE CommercialProperty (
    property_id INT PRIMARY KEY,
    sqft DECIMAL(10, 2),
    industry VARCHAR(255),
    c_type VARCHAR(50),  -- Retail, Office, Industrial, etc.
    num_units INT,
    parking_spaces INT,
    zoning_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES Property(property_id) ON DELETE CASCADE
);

-- Agent Listing Table
DROP TABLE IF EXISTS AgentListing;
CREATE TABLE AgentListing (
    listing_id INT PRIMARY KEY AUTO_INCREMENT,
    property_id INT NOT NULL,
    agent_id INT NOT NULL,
    client_id INT NOT NULL,  -- seller/owner
    agent_role ENUM('SellerAgent') NOT NULL,
    listing_date DATE NOT NULL,
    expiration_date DATE,
    exclusive BOOLEAN NOT NULL,
    asking_price DECIMAL(15, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES Property(property_id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES Agent(agent_id),
    FOREIGN KEY (client_id) REFERENCES Client(client_id),
    INDEX idx_listing_date (listing_date)
);

CREATE TABLE PropertyImages (
    image_id INT PRIMARY KEY AUTO_INCREMENT,
    property_id INT NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES Property(property_id) ON DELETE CASCADE
);

-- Agent Showing Table
DROP TABLE IF EXISTS AgentShowing;
CREATE TABLE AgentShowing (
    showing_id INT PRIMARY KEY AUTO_INCREMENT,
    property_id INT NOT NULL,
    agent_id INT NOT NULL,
    client_id INT NOT NULL,  -- potential buyer/lessee
    agent_role ENUM('BuyerAgent', 'LesseeAgent') NOT NULL,
    showing_date DATE NOT NULL,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES Property(property_id),
    FOREIGN KEY (agent_id) REFERENCES Agent(agent_id),
    FOREIGN KEY (client_id) REFERENCES Client(client_id),
    INDEX idx_showing_date (showing_date)
);

-- Contract Table
DROP TABLE IF EXISTS Contract;
CREATE TABLE Contract (
    contract_id INT PRIMARY KEY AUTO_INCREMENT,
    property_id INT NOT NULL,
    client_id INT NOT NULL,
    agent_id INT NOT NULL,
    contract_type ENUM('Listing', 'Showing') NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    terms TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES Property(property_id),
    FOREIGN KEY (client_id) REFERENCES Client(client_id),
    FOREIGN KEY (agent_id) REFERENCES Agent(agent_id)
);

-- Transaction Table
DROP TABLE IF EXISTS Transaction;
CREATE TABLE Transaction (
    transaction_id INT PRIMARY KEY AUTO_INCREMENT,
    property_id INT NOT NULL,
    seller_id INT NOT NULL,
    buyer_id INT NOT NULL,
    agent_id INT NOT NULL,
    transaction_date DATE NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    transaction_type ENUM('Sale', 'Lease') NOT NULL,
    commission_amount DECIMAL(15, 2),
    closing_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES Property(property_id),
    FOREIGN KEY (seller_id) REFERENCES Client(client_id),
    FOREIGN KEY (buyer_id) REFERENCES Client(client_id),
    FOREIGN KEY (agent_id) REFERENCES Agent(agent_id),
    INDEX idx_transaction_date (transaction_date)
);

SET FOREIGN_KEY_CHECKS=1;
