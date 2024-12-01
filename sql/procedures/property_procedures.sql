DELIMITER //

DELIMITER //

CREATE PROCEDURE get_all_properties_with_details()
BEGIN
    SELECT 
        p.*,
        -- Residential details
        rp.bedrooms,
        rp.bathrooms,
        rp.r_type,
        rp.square_feet,
        rp.garage_spaces,
        rp.has_basement,
        rp.has_pool,
        -- Commercial details
        cp.sqft,
        cp.industry,
        cp.c_type,
        cp.num_units,
        cp.parking_spaces,
        cp.zoning_type,
        -- Agent details
        a.agent_id,
        a.agent_name,
        a.agent_phone,
        al.l_agent_role,
        al.exclusive
    FROM Property p
    LEFT JOIN ResidentialProperty rp ON p.tax_id = rp.tax_id
    LEFT JOIN CommercialProperty cp ON p.tax_id = cp.tax_id
    LEFT JOIN AgentListing al ON p.tax_id = al.tax_id
    LEFT JOIN Agent a ON al.agent_id = a.agent_id
    WHERE p.status IN ('For Sale', 'For Lease')
    ORDER BY p.tax_id DESC;
END //

DROP PROCEDURE IF EXISTS get_all_properties;
CREATE PROCEDURE get_all_properties()
BEGIN
    SELECT 
        property_id,
        tax_id,
        property_address,
        status,
        price,
        lot_size,
        year_built,
        zoning,
        property_tax,
        created_at,
        updated_at
    FROM Property
    ORDER BY created_at DESC;
END //

-- Create property
DROP PROCEDURE IF EXISTS create_property;
CREATE PROCEDURE create_property(
    IN p_tax_id VARCHAR(50),
    IN p_property_address VARCHAR(255),
    IN p_status ENUM('For Sale', 'For Lease', 'Sold', 'Leased'),
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
    IN p_zoning_type VARCHAR(50)
)
BEGIN
    DECLARE new_property_id INT;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Validate inputs
    IF p_year_built > YEAR(CURDATE()) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Year built cannot be in the future';
    END IF;

    IF p_price <= 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Price must be greater than zero';
    END IF;

    -- Insert base property record
    INSERT INTO Property (
        tax_id,
        property_address,
        status,
        price,
        lot_size,
        year_built,
        zoning,
        property_tax,
        created_at,
        updated_at -- Use updated_at instead of last_modified
    ) VALUES (
        p_tax_id,
        p_property_address,
        p_status,
        p_price,
        p_lot_size,
        p_year_built,
        p_zoning,
        p_property_tax,
        NOW(),
        NOW() -- Provide the same value for both created_at and updated_at initially
    );

    SET new_property_id = LAST_INSERT_ID();

    -- Insert type-specific details
    IF p_property_type = 'RESIDENTIAL' THEN
        IF p_bedrooms <= 0 OR p_bathrooms <= 0 OR p_square_feet <= 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid residential property specifications';
        END IF;

        INSERT INTO ResidentialProperty (
            property_id,
            bedrooms,
            bathrooms,
            r_type,
            square_feet,
            garage_spaces,
            has_basement,
            has_pool
        ) VALUES (
            new_property_id,
            p_bedrooms,
            p_bathrooms,
            p_r_type,
            p_square_feet,
            p_garage_spaces,
            p_has_basement,
            p_has_pool
        );
    ELSEIF p_property_type = 'COMMERCIAL' THEN
        IF p_sqft <= 0 OR p_parking_spaces < 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid commercial property specifications';
        END IF;

        INSERT INTO CommercialProperty (
            property_id,
            sqft,
            industry,
            c_type,
            num_units,
            parking_spaces,
            zoning_type
        ) VALUES (
            new_property_id,
            p_sqft,
            p_industry,
            p_c_type,
            p_num_units,
            p_parking_spaces,
            p_zoning_type
        );
    ELSE
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Invalid property type';
    END IF;

    COMMIT;

    -- Return the created property details
    CALL get_property_details(new_property_id);
END //

-- Get property details
DROP PROCEDURE IF EXISTS get_property_details;
CREATE PROCEDURE get_property_details(IN p_property_id INT)
BEGIN
    SELECT 
        p.*,
        -- Agent details
        a.agent_id,
        a.agent_name,
        a.agent_phone,
        -- Residential details
        rp.bedrooms,
        rp.bathrooms,
        rp.r_type,
        rp.square_feet,
        rp.garage_spaces,
        rp.has_basement,
        rp.has_pool,
        -- Commercial details
        c.sqft,
        c.industry,
        c.c_type,
        c.num_units,
        c.parking_spaces,
        c.zoning_type
    FROM Property p
    LEFT JOIN AgentListing al ON p.property_id = al.property_id
    LEFT JOIN Agent a ON al.agent_id = a.agent_id
    LEFT JOIN ResidentialProperty rp ON p.property_id = rp.property_id
    LEFT JOIN CommercialProperty c ON p.property_id = c.property_id
    WHERE p.property_id = p_property_id;
END //

-- Search properties

DROP PROCEDURE IF EXISTS search_properties;
CREATE PROCEDURE search_properties(
    IN p_min_price DECIMAL(10, 2),
    IN p_max_price DECIMAL(10, 2),
    IN p_page INT,
    IN p_page_size INT,
    IN p_sort_by VARCHAR(50),
    IN p_sort_direction VARCHAR(4)
)
BEGIN
    -- All DECLARE statements must be at the start of the BEGIN block
    DECLARE v_offset INT;
    DECLARE v_sort_clause VARCHAR(100);

    -- Calculate offset for pagination
    SET v_offset = (p_page - 1) * p_page_size;

    -- Build dynamic sort clause
    SET v_sort_clause = CASE 
        WHEN p_sort_by IS NULL THEN 'p.created_at DESC'
        ELSE CONCAT(p_sort_by, ' ', COALESCE(p_sort_direction, 'ASC'))
    END;

    -- Execute the query
    SET @query = CONCAT(
        'SELECT p.*, ',
        '       CASE ',
        '           WHEN r.property_id IS NOT NULL THEN ''RESIDENTIAL'' ',
        '           WHEN c.property_id IS NOT NULL THEN ''COMMERCIAL'' ',
        '       END AS property_type, ',
        '       r.bedrooms, ',
        '       r.bathrooms, ',
        '       r.square_feet AS residential_sqft, ',
        '       r.has_pool, ',
        '       r.has_basement, ',
        '       c.sqft AS commercial_sqft, ',
        '       c.num_units, ',
        '       al.asking_price AS current_asking_price, ',
        '       a.agent_name AS listing_agent, ',
        '       pi.file_path AS primary_image ',
        'FROM Properties p ',
        'LEFT JOIN ResidentialProperty r ON p.property_id = r.property_id ',
        'LEFT JOIN CommercialProperty c ON p.property_id = c.property_id ',
        'LEFT JOIN AgentListing al ON p.property_id = al.property_id ',
        '       AND al.expiration_date > CURDATE() ',
        'LEFT JOIN Agents a ON al.agent_id = a.agent_id ',
        'LEFT JOIN PropertyImages pi ON p.property_id = pi.property_id ',
        '       AND pi.is_primary = TRUE ',
        'WHERE (p_min_price IS NULL OR p.price >= p_min_price) ',
        '  AND (p_max_price IS NULL OR p.price <= p_max_price) ',
        'ORDER BY ', v_sort_clause, ' ',
        'LIMIT ', p_page_size, ' OFFSET ', v_offset
    );

    PREPARE stmt FROM @query;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END //

-- Update property
DROP PROCEDURE IF EXISTS update_property;
CREATE PROCEDURE update_property(
    IN p_property_id INT,
    IN p_tax_id VARCHAR(50),
    IN p_property_address VARCHAR(255),
    IN p_status VARCHAR(20),
    IN p_price DECIMAL(15, 2),
    IN p_lot_size DECIMAL(10, 2),
    IN p_year_built INT,
    IN p_zoning VARCHAR(50),
    IN p_property_tax DECIMAL(10, 2),
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
    IN p_zoning_type VARCHAR(50)
)
BEGIN
    DECLARE v_property_type VARCHAR(20);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;
    
    -- Determine property type
    SELECT 
        CASE 
            WHEN r.property_id IS NOT NULL THEN 'RESIDENTIAL'
            WHEN c.property_id IS NOT NULL THEN 'COMMERCIAL'
        END INTO v_property_type
    FROM Property p
    LEFT JOIN ResidentialProperty r ON p.property_id = r.property_id
    LEFT JOIN CommercialProperty c ON p.property_id = c.property_id
    WHERE p.property_id = p_property_id;

    -- Update base property information
    UPDATE Property 
    SET 
        tax_id = COALESCE(p_tax_id, tax_id),
        property_address = COALESCE(p_property_address, property_address),
        status = COALESCE(p_status, status),
        price = COALESCE(p_price, price),
        lot_size = COALESCE(p_lot_size, lot_size),
        year_built = COALESCE(p_year_built, year_built),
        zoning = COALESCE(p_zoning, zoning),
        property_tax = COALESCE(p_property_tax, property_tax),
        last_modified = NOW()
    WHERE property_id = p_property_id;

    -- Update type-specific information
    IF v_property_type = 'RESIDENTIAL' THEN
        UPDATE ResidentialProperty 
        SET 
            bedrooms = COALESCE(p_bedrooms, bedrooms),
            bathrooms = COALESCE(p_bathrooms, bathrooms),
            r_type = COALESCE(p_r_type, r_type),
            square_feet = COALESCE(p_square_feet, square_feet),
            garage_spaces = COALESCE(p_garage_spaces, garage_spaces),
            has_basement = COALESCE(p_has_basement, has_basement),
            has_pool = COALESCE(p_has_pool, has_pool)
        WHERE property_id = p_property_id;
    ELSEIF v_property_type = 'COMMERCIAL' THEN
        UPDATE CommercialProperty 
        SET 
            sqft = COALESCE(p_sqft, sqft),
            industry = COALESCE(p_industry, industry),
            c_type = COALESCE(p_c_type, c_type),
            num_units = COALESCE(p_num_units, num_units),
            parking_spaces = COALESCE(p_parking_spaces, parking_spaces),
            zoning_type = COALESCE(p_zoning_type, zoning_type)
        WHERE property_id = p_property_id;
    ELSE
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Invalid property type for update';
    END IF;

    COMMIT;
END //
