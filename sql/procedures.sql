DELIMITER //

CREATE PROCEDURE add_property_image(
    IN p_property_id INT,
    IN p_file_path VARCHAR(255),
    IN p_is_primary BOOLEAN
)
BEGIN
    -- If this is primary, unset any existing primary
    IF p_is_primary THEN
        UPDATE PropertyImages 
        SET is_primary = FALSE 
        WHERE property_id = p_property_id;
    END IF;

    INSERT INTO PropertyImages (property_id, file_path, is_primary)
    VALUES (p_property_id, p_file_path, p_is_primary);
END //

CREATE PROCEDURE get_property_images(IN p_property_id INT)
BEGIN
    SELECT * FROM PropertyImages
    WHERE property_id = p_property_id
    ORDER BY is_primary DESC, uploaded_at DESC;
END //

DELIMITER ;


DELIMITER / /

CREATE PROCEDURE delete_property(
    IN p_property_id INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;
    
    -- Delete type-specific details first (due to foreign key constraints)
    DELETE FROM ResidentialProperty WHERE property_id = p_property_id;
    DELETE FROM CommercialProperty WHERE property_id = p_property_id;
    
    -- Delete from related tables
    DELETE FROM AgentListing WHERE property_id = p_property_id;
    DELETE FROM AgentShowing WHERE property_id = p_property_id;
    DELETE FROM Contract WHERE property_id = p_property_id;
    DELETE FROM Transaction WHERE property_id = p_property_id;
    
    -- Finally delete the property itself
    DELETE FROM Property WHERE property_id = p_property_id;
    
    COMMIT;
END //

DELIMITER ;

DELIMITER / / 

CREATE PROCEDURE create_property (
  IN p_tax_id VARCHAR(50),
  IN p_property_address VARCHAR(255),
  IN p_status ENUM ('For Sale', 'For Lease', 'Sold', 'Leased'),
  IN p_price DECIMAL(15, 2),
  IN p_lot_size DECIMAL(10, 2),
  IN p_year_built INT,
  IN p_zoning VARCHAR(50),
  IN p_property_tax DECIMAL(10, 2),
  IN p_property_type VARCHAR(20),
  -- Residential specific parameters
  IN p_bedrooms INT,
  IN p_bathrooms DECIMAL(3, 1),
  IN p_r_type VARCHAR(50),
  IN p_square_feet DECIMAL(10, 2),
  IN p_garage_spaces INT,
  IN p_has_basement BOOLEAN,
  IN p_has_pool BOOLEAN,
  -- Commercial specific parameters
  IN p_sqft DECIMAL(10, 2),
  IN p_industry VARCHAR(255),
  IN p_c_type VARCHAR(50),
  IN p_num_units INT,
  IN p_parking_spaces INT,
  IN p_zoning_type VARCHAR(50),
  OUT p_property_id INT
) BEGIN DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK;

RESIGNAL;

END;

START TRANSACTION;

-- Insert base property
INSERT INTO
  Property (
    tax_id,
    property_address,
    status,
    price,
    lot_size,
    year_built,
    zoning,
    property_tax
  )
VALUES
  (
    p_tax_id,
    p_property_address,
    p_status,
    p_price,
    p_lot_size,
    p_year_built,
    p_zoning,
    p_property_tax
  );

SET
  p_property_id = LAST_INSERT_ID ();

-- Insert type-specific details
IF p_property_type = 'RESIDENTIAL' THEN
INSERT INTO
  ResidentialProperty (
    property_id,
    bedrooms,
    bathrooms,
    r_type,
    square_feet,
    garage_spaces,
    has_basement,
    has_pool
  )
VALUES
  (
    p_property_id,
    p_bedrooms,
    p_bathrooms,
    p_r_type,
    p_square_feet,
    p_garage_spaces,
    p_has_basement,
    p_has_pool
  );

ELSEIF p_property_type = 'COMMERCIAL' THEN
INSERT INTO
  CommercialProperty (
    property_id,
    sqft,
    industry,
    c_type,
    num_units,
    parking_spaces,
    zoning_type
  )
VALUES
  (
    p_property_id,
    p_sqft,
    p_industry,
    p_c_type,
    p_num_units,
    p_parking_spaces,
    p_zoning_type
  );

END IF;

COMMIT;

END / / DELIMITER;

DELIMITER / /
-- Get property details with all related information
CREATE PROCEDURE get_property_details (IN p_id INT) BEGIN
SELECT
  p.*,
  CASE
    WHEN r.property_id IS NOT NULL THEN 'Residential'
    WHEN c.property_id IS NOT NULL THEN 'Commercial'
  END as property_type,
  r.bedrooms,
  r.bathrooms,
  r.r_type,
  r.square_feet as residential_sqft,
  r.garage_spaces,
  r.has_basement,
  r.has_pool,
  c.sqft as commercial_sqft,
  c.industry,
  c.c_type,
  c.num_units,
  c.parking_spaces,
  c.zoning_type,
  a.agent_name as listing_agent,
  a.agent_phone,
  a.agent_email,
  b.broker_name,
  b.broker_phone,
  cl.client_name as owner_name
FROM
  Property p
  LEFT JOIN ResidentialProperty r ON p.property_id = r.property_id
  LEFT JOIN CommercialProperty c ON p.property_id = c.property_id
  LEFT JOIN AgentListing al ON p.property_id = al.property_id
  LEFT JOIN Agent a ON al.agent_id = a.agent_id
  LEFT JOIN Brokerage b ON a.broker_id = b.broker_id
  LEFT JOIN Client cl ON al.client_id = cl.client_id
WHERE
  p.property_id = p_id;

END / /
-- Search properties with filters
CREATE PROCEDURE search_properties (
  IN min_price DECIMAL(15, 2),
  IN max_price DECIMAL(15, 2),
  IN p_status VARCHAR(20),
  IN property_type VARCHAR(20),
  IN min_beds INT,
  IN min_baths DECIMAL(3, 1),
  IN max_distance INT,
  IN reference_location VARCHAR(255)
) BEGIN
SELECT
  p.*,
  r.bedrooms,
  r.bathrooms,
  r.r_type,
  c.sqft,
  c.c_type,
  a.agent_name,
  a.agent_phone
FROM
  Property p
  LEFT JOIN ResidentialProperty r ON p.property_id = r.property_id
  LEFT JOIN CommercialProperty c ON p.property_id = c.property_id
  LEFT JOIN AgentListing al ON p.property_id = al.property_id
  LEFT JOIN Agent a ON al.agent_id = a.agent_id
WHERE
  (
    min_price IS NULL
    OR p.price >= min_price
  )
  AND (
    max_price IS NULL
    OR p.price <= max_price
  )
  AND (
    p_status IS NULL
    OR p.status = p_status
  )
  AND (
    property_type IS NULL
    OR (
      property_type = 'Residential'
      AND r.property_id IS NOT NULL
    )
    OR (
      property_type = 'Commercial'
      AND c.property_id IS NOT NULL
    )
  )
  AND (
    min_beds IS NULL
    OR r.bedrooms >= min_beds
  )
  AND (
    min_baths IS NULL
    OR r.bathrooms >= min_baths
  )
ORDER BY
  p.created_at DESC;

END / /
-- Get agent performance metrics
CREATE PROCEDURE get_agent_performance (
  IN agent_id INT,
  IN start_date DATE,
  IN end_date DATE
) BEGIN
SELECT
  a.agent_id,
  a.agent_name,
  COUNT(DISTINCT al.listing_id) as active_listings,
  COUNT(DISTINCT ash.showing_id) as showings_conducted,
  COUNT(DISTINCT t.transaction_id) as transactions_closed,
  SUM(
    CASE
      WHEN t.transaction_type = 'Sale' THEN t.amount
      ELSE 0
    END
  ) as total_sales_volume,
  SUM(
    CASE
      WHEN t.transaction_type = 'Lease' THEN t.amount
      ELSE 0
    END
  ) as total_lease_volume,
  SUM(t.commission_amount) as total_commission,
  AVG(
    CASE
      WHEN t.transaction_type = 'Sale' THEN t.amount
      ELSE NULL
    END
  ) as avg_sale_price,
  COUNT(
    DISTINCT CASE
      WHEN t.transaction_type = 'Sale' THEN t.transaction_id
    END
  ) as num_sales,
  COUNT(
    DISTINCT CASE
      WHEN t.transaction_type = 'Lease' THEN t.transaction_id
    END
  ) as num_leases
FROM
  Agent a
  LEFT JOIN AgentListing al ON a.agent_id = al.agent_id
  AND (
    start_date IS NULL
    OR al.listing_date >= start_date
  )
  AND (
    end_date IS NULL
    OR al.listing_date <= end_date
  )
  LEFT JOIN AgentShowing ash ON a.agent_id = ash.agent_id
  AND (
    start_date IS NULL
    OR ash.showing_date >= start_date
  )
  AND (
    end_date IS NULL
    OR ash.showing_date <= end_date
  )
  LEFT JOIN Transaction t ON a.agent_id = t.agent_id
  AND (
    start_date IS NULL
    OR t.transaction_date >= start_date
  )
  AND (
    end_date IS NULL
    OR t.transaction_date <= end_date
  )
WHERE
  a.agent_id = agent_id
GROUP BY
  a.agent_id,
  a.agent_name;

END / /
-- Get client portfolio summary
CREATE PROCEDURE get_client_portfolio (IN client_id INT) BEGIN
SELECT
  c.client_id,
  c.client_name,
  c.client_phone,
  c.client_email,
  GROUP_CONCAT (DISTINCT cr.role) as roles,
  COUNT(
    DISTINCT CASE
      WHEN t.seller_id = c.client_id THEN t.transaction_id
    END
  ) as properties_sold,
  COUNT(
    DISTINCT CASE
      WHEN t.buyer_id = c.client_id THEN t.transaction_id
    END
  ) as properties_bought,
  SUM(
    CASE
      WHEN t.seller_id = c.client_id THEN t.amount
      ELSE 0
    END
  ) as total_sales,
  SUM(
    CASE
      WHEN t.buyer_id = c.client_id THEN t.amount
      ELSE 0
    END
  ) as total_purchases,
  COUNT(DISTINCT al.listing_id) as active_listings,
  COUNT(DISTINCT ash.showing_id) as property_viewings
FROM
  Client c
  LEFT JOIN ClientRoles cr ON c.client_id = cr.client_id
  LEFT JOIN Transaction t ON c.client_id = t.seller_id
  OR c.client_id = t.buyer_id
  LEFT JOIN AgentListing al ON c.client_id = al.client_id
  LEFT JOIN AgentShowing ash ON c.client_id = ash.client_id
WHERE
  c.client_id = client_id
GROUP BY
  c.client_id,
  c.client_name,
  c.client_phone,
  c.client_email;

END / /
-- Create new listing with checks
CREATE PROCEDURE create_listing (
  IN p_property_id INT,
  IN p_agent_id INT,
  IN p_client_id INT,
  IN p_agent_role VARCHAR(20),
  IN p_listing_date DATE,
  IN p_expiration_date DATE,
  IN p_asking_price DECIMAL(15, 2),
  IN p_exclusive BOOLEAN,
  OUT p_listing_id INT
) BEGIN DECLARE existing_listing INT;

-- Check if property already has an active listing
SELECT
  listing_id INTO existing_listing
FROM
  AgentListing
WHERE
  property_id = p_property_id
  AND expiration_date > CURRENT_DATE();

IF existing_listing IS NOT NULL THEN SIGNAL SQLSTATE '45000'
SET
  MESSAGE_TEXT = 'Property already has an active listing';

END IF;

-- Create the listing
INSERT INTO
  AgentListing (
    property_id,
    agent_id,
    client_id,
    agent_role,
    listing_date,
    expiration_date,
    asking_price,
    exclusive
  )
VALUES
  (
    p_property_id,
    p_agent_id,
    p_client_id,
    p_agent_role,
    p_listing_date,
    p_expiration_date,
    p_asking_price,
    p_exclusive
  );

SET
  p_listing_id = LAST_INSERT_ID ();

END / /
-- Record property showing
CREATE PROCEDURE record_showing (
  IN p_property_id INT,
  IN p_agent_id INT,
  IN p_client_id INT,
  IN p_agent_role VARCHAR(20),
  IN p_showing_date DATE,
  IN p_feedback TEXT,
  OUT p_showing_id INT
) BEGIN
INSERT INTO
  AgentShowing (
    property_id,
    agent_id,
    client_id,
    agent_role,
    showing_date,
    feedback
  )
VALUES
  (
    p_property_id,
    p_agent_id,
    p_client_id,
    p_agent_role,
    p_showing_date,
    p_feedback
  );

SET
  p_showing_id = LAST_INSERT_ID ();

END / /
-- Record transaction
CREATE PROCEDURE record_transaction (
  IN p_property_id INT,
  IN p_seller_id INT,
  IN p_buyer_id INT,
  IN p_agent_id INT,
  IN p_amount DECIMAL(15, 2),
  IN p_transaction_type VARCHAR(10),
  IN p_commission_amount DECIMAL(15, 2),
  IN p_closing_date DATE
) BEGIN START TRANSACTION;

-- Record the transaction
INSERT INTO
  Transaction (
    property_id,
    seller_id,
    buyer_id,
    agent_id,
    transaction_date,
    amount,
    transaction_type,
    commission_amount,
    closing_date
  )
VALUES
  (
    p_property_id,
    p_seller_id,
    p_buyer_id,
    p_agent_id,
    CURRENT_DATE(),
    p_amount,
    p_transaction_type,
    p_commission_amount,
    p_closing_date
  );

-- Update property status
UPDATE Property
SET
  status = CASE
    WHEN p_transaction_type = 'Sale' THEN 'Sold'
    WHEN p_transaction_type = 'Lease' THEN 'Leased'
  END
WHERE
  property_id = p_property_id;

-- Close any active listings
UPDATE AgentListing
SET
  expiration_date = CURRENT_DATE()
WHERE
  property_id = p_property_id
  AND expiration_date > CURRENT_DATE();

COMMIT;

END / /
-- Get market analysis
CREATE PROCEDURE get_market_analysis (
  IN start_date DATE,
  IN end_date DATE,
  IN property_type VARCHAR(20)
) BEGIN
SELECT
  COUNT(DISTINCT t.transaction_id) as total_transactions,
  SUM(
    CASE
      WHEN t.transaction_type = 'Sale' THEN 1
      ELSE 0
    END
  ) as total_sales,
  SUM(
    CASE
      WHEN t.transaction_type = 'Lease' THEN 1
      ELSE 0
    END
  ) as total_leases,
  AVG(
    CASE
      WHEN t.transaction_type = 'Sale' THEN t.amount
    END
  ) as avg_sale_price,
  AVG(
    CASE
      WHEN t.transaction_type = 'Lease' THEN t.amount
    END
  ) as avg_lease_price,
  MIN(
    CASE
      WHEN t.transaction_type = 'Sale' THEN t.amount
    END
  ) as min_sale_price,
  MAX(
    CASE
      WHEN t.transaction_type = 'Sale' THEN t.amount
    END
  ) as max_sale_price,
  AVG(DATEDIFF (t.closing_date, al.listing_date)) as avg_days_on_market,
  COUNT(DISTINCT p.property_id) as active_listings,
  AVG(p.price) as avg_listing_price
FROM
  Transaction t
  JOIN Property p ON t.property_id = p.property_id
  LEFT JOIN ResidentialProperty r ON p.property_id = r.property_id
  LEFT JOIN CommercialProperty c ON p.property_id = c.property_id
  LEFT JOIN AgentListing al ON t.property_id = al.property_id
WHERE
  (
    start_date IS NULL
    OR t.transaction_date >= start_date
  )
  AND (
    end_date IS NULL
    OR t.transaction_date <= end_date
  )
  AND (
    property_type IS NULL
    OR (
      property_type = 'Residential'
      AND r.property_id IS NOT NULL
    )
    OR (
      property_type = 'Commercial'
      AND c.property_id IS NOT NULL
    )
  );

END / / DELIMITER;
