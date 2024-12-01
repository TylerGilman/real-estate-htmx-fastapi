-- Drop the database if it exists and create a fresh one
DROP DATABASE IF EXISTS real_estate;
CREATE DATABASE real_estate;
USE real_estate;

-- Reset database
SOURCE schema.sql;

-- Source all procedure files
SOURCE procedures/auth_procedures.sql
SOURCE procedures/agent_procedures.sql
SOURCE procedures/property_procedures.sql
SOURCE procedures/client_procedures.sql
SOURCE procedures/listing_procedures.sql
SOURCE procedures/transaction_procedures.sql
SOURCE procedures/dashboard_procedures.sql

-- Insert brokerage
INSERT INTO Brokerage (
    broker_name,
    broker_address,
    broker_phone,
    broker_email,
    broker_license
) VALUES (
    'Cherokee Street Real Estate',
    '25 Cherokee St, Boston, MA',
    '555-123-4567',
    'contact@cherokeerealestate.com',
    'LIC-2023-001'
);

-- Insert sample clients
INSERT INTO Client (
    client_name,
    SSN,
    mailing_address,
    client_phone,
    client_email
) VALUES 
('Sarah Johnson', '123-45-6789', '789 Oak Lane, Boston, MA', '555-111-3333', 'sarah.j@email.com'),
('Michael Brown', '234-56-7890', '456 Pine Ave, Boston, MA', '555-222-4444', 'michael.b@email.com'),
('Lisa Wilson', '345-67-8901', '123 Maple St, Boston, MA', '555-333-5555', 'lisa.w@email.com');

-- Insert client roles
INSERT INTO ClientRoles (client_id, role)
SELECT client_id, 'Seller' FROM Client WHERE client_name = 'Sarah Johnson';

-- Insert sample agents
INSERT INTO Agent (
    NRDS,
    agent_name,
    agent_phone,
    agent_email,
    SSN,
    broker_id,
    license_number,
    license_expiration
) VALUES 
(
    '7654321',
    'John Smith',
    '555-111-2222',
    'john.smith@cherokeerealestate.com',
    '987-65-4321',
    LAST_INSERT_ID(),
    'AG2023001',
    DATE_ADD(CURRENT_DATE, INTERVAL 1 YEAR)
),
(
    '7654322',
    'Jane Doe',
    '555-333-4444',
    'jane.doe@cherokeerealestate.com',
    '876-54-3210',
    LAST_INSERT_ID(),
    'AG2023002',
    DATE_ADD(CURRENT_DATE, INTERVAL 1 YEAR)
),
(
    '7654323',
    'Bob Wilson',
    '555-555-6666',
    'bob.wilson@cherokeerealestate.com',
    '765-43-2109',
    LAST_INSERT_ID(),
    'AG2023003',
    DATE_ADD(CURRENT_DATE, INTERVAL 1 YEAR)
);

-- Create agent users
INSERT INTO User (
    username,
    password_hash,
    role_id,
    agent_id
)
SELECT 
    LOWER(SUBSTRING_INDEX(agent_name, ' ', 1)), -- First name as username
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYpfQN5Mb7pmZbu', -- Same password as admin
    (SELECT role_id FROM UserRole WHERE role_name = 'agent'),
    agent_id
FROM Agent;

-- Insert properties
INSERT INTO Property (
    tax_id,
    property_address,
    status,
    price,
    lot_size,
    year_built,
    zoning,
    property_tax
) VALUES 
('TAX001', '123 Main St, Boston, MA', 'For Sale', 500000.00, 5000.00, 1990, 'Residential', 5000.00),
('TAX002', '456 Oak Ave, Boston, MA', 'For Lease', 750000.00, 10000.00, 2000, 'Commercial', 7500.00),
('TAX003', '789 Pine St, Boston, MA', 'For Sale', 350000.00, 4000.00, 1985, 'Residential', 3500.00);

-- Add residential details
INSERT INTO ResidentialProperty (
    property_id,
    bedrooms,
    bathrooms,
    r_type,
    square_feet,
    garage_spaces,
    has_basement,
    has_pool
) 
SELECT 
    property_id,
    3,
    2.5,
    'Single Family',
    2000,
    2,
    true,
    false
FROM Property
WHERE property_address LIKE '%Main St%' OR property_address LIKE '%Pine St%';

-- Add commercial details
INSERT INTO CommercialProperty (
    property_id,
    sqft,
    industry,
    c_type,
    num_units,
    parking_spaces,
    zoning_type
)
SELECT 
    property_id,
    10000,
    'Retail',
    'Shopping Center',
    5,
    20,
    'C-1'
FROM Property
WHERE property_address LIKE '%Oak Ave%';

-- Create agent listings
INSERT INTO AgentListing (
    property_id,
    agent_id,
    client_id,
    agent_role,
    listing_date,
    exclusive,
    asking_price
)
SELECT 
    p.property_id,
    (SELECT agent_id FROM Agent ORDER BY RAND() LIMIT 1),
    (SELECT client_id FROM Client ORDER BY RAND() LIMIT 1),
    'SellerAgent',
    CURRENT_DATE,
    true,
    p.price
FROM Property p;
