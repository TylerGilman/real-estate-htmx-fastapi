DELIMITER //

-- Create new agent
CREATE PROCEDURE create_agent(
    IN p_agent_name VARCHAR(255),
    IN p_NRDS VARCHAR(50),
    IN p_agent_phone VARCHAR(15),
    IN p_agent_email VARCHAR(255),
    IN p_SSN VARCHAR(15),
    IN p_license_number VARCHAR(50),
    IN p_license_expiration DATE,
    IN p_broker_id INT,
    IN p_commission_rate DECIMAL(5,2),
    IN p_hire_date DATE
)
BEGIN
    DECLARE new_agent_id INT;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Validate inputs
    IF p_license_expiration <= CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'License must be valid and not expired';
    END IF;

    IF p_agent_email NOT REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Invalid email format';
    END IF;

    INSERT INTO Agent (
        agent_name,
        NRDS,
        agent_phone,
        agent_email,
        SSN,
        license_number,
        license_expiration,
        broker_id,
        commission_rate,
        hire_date,
        created_at,
        last_modified
    ) VALUES (
        p_agent_name,
        p_NRDS,
        p_agent_phone,
        p_agent_email,
        p_SSN,
        p_license_number,
        p_license_expiration,
        p_broker_id,
        p_commission_rate,
        p_hire_date,
        NOW(),
        NOW()
    );

    SET new_agent_id = LAST_INSERT_ID();

    COMMIT;

    -- Return created agent
    SELECT 
        a.*,
        b.broker_name,
        b.broker_license
    FROM Agent a
    JOIN Brokerage b ON a.broker_id = b.broker_id
    WHERE a.agent_id = new_agent_id;
END //

-- Get all agents with summary info
CREATE PROCEDURE get_all_agents(
    IN p_page INT,
    IN p_page_size INT,
    IN p_sort_field VARCHAR(50),
    IN p_sort_direction VARCHAR(4)
)
BEGIN
    DECLARE v_offset INT;
    DECLARE v_sort_clause VARCHAR(100);
    
    SET v_offset = (p_page - 1) * p_page_size;
    SET v_sort_clause = CASE 
        WHEN p_sort_field IS NULL THEN 'a.created_at DESC'
        ELSE CONCAT(p_sort_field, ' ', COALESCE(p_sort_direction, 'ASC'))
    END;

    -- Get total count for pagination
    SELECT COUNT(*) as total_count FROM Agent;

    -- Get agents with summary metrics
    SET @sql = CONCAT('
    SELECT 
        a.*,
        b.broker_name,
        COUNT(DISTINCT al.listing_id) as active_listings,
        COUNT(DISTINCT t.transaction_id) as total_transactions,
        COALESCE(SUM(t.amount), 0) as total_sales_volume,
        COALESCE(SUM(t.commission_amount), 0) as total_commission,
        DATEDIFF(a.license_expiration, CURDATE()) as days_until_license_expiry
    FROM Agent a
    JOIN Brokerage b ON a.broker_id = b.broker_id
    LEFT JOIN AgentListing al ON a.agent_id = al.agent_id 
        AND al.expiration_date > CURDATE()
    LEFT JOIN Transaction t ON a.agent_id = t.agent_id
    GROUP BY a.agent_id
    ORDER BY ', v_sort_clause, '
    LIMIT ? OFFSET ?');

    PREPARE stmt FROM @sql;
    EXECUTE stmt USING p_page_size, v_offset;
    DEALLOCATE PREPARE stmt;
END //

-- Get specific agent details
CREATE PROCEDURE get_agent_details(
    IN p_agent_id INT
)
BEGIN
    -- Get main agent info
    SELECT 
        a.*,
        b.broker_name,
        b.broker_license,
        COUNT(DISTINCT al.listing_id) as active_listings,
        COUNT(DISTINCT t.transaction_id) as total_transactions,
        COALESCE(SUM(t.amount), 0) as total_sales_volume,
        COALESCE(SUM(t.commission_amount), 0) as total_commission,
        DATEDIFF(a.license_expiration, CURDATE()) as days_until_license_expiry
    FROM Agent a
    JOIN Brokerage b ON a.broker_id = b.broker_id
    LEFT JOIN AgentListing al ON a.agent_id = al.agent_id 
        AND al.expiration_date > CURDATE()
    LEFT JOIN Transaction t ON a.agent_id = t.agent_id
    WHERE a.agent_id = p_agent_id
    GROUP BY a.agent_id;

    -- Get active listings
    SELECT 
        p.*,
        al.asking_price,
        al.listing_date,
        al.expiration_date,
        c.client_name as owner_name,
        pi.file_path as primary_image
    FROM AgentListing al
    JOIN Property p ON al.property_id = p.property_id
    JOIN Client c ON al.client_id = c.client_id
    LEFT JOIN PropertyImages pi ON p.property_id = pi.property_id 
        AND pi.is_primary = TRUE
    WHERE al.agent_id = p_agent_id
    AND al.expiration_date > CURDATE();

    -- Get recent transactions
    SELECT 
        t.*,
        p.property_address,
        s.client_name as seller_name,
        b.client_name as buyer_name
    FROM Transaction t
    JOIN Property p ON t.property_id = p.property_id
    JOIN Client s ON t.seller_id = s.client_id
    JOIN Client b ON t.buyer_id = b.client_id
    WHERE t.agent_id = p_agent_id
    ORDER BY t.transaction_date DESC
    LIMIT 10;

    -- Get performance metrics
    SELECT 
        COUNT(DISTINCT CASE WHEN t.transaction_type = 'SALE' THEN t.transaction_id END) as total_sales,
        COUNT(DISTINCT CASE WHEN t.transaction_type = 'LEASE' THEN t.transaction_id END) as total_leases,
        AVG(t.amount) as avg_transaction_value,
        AVG(t.commission_amount) as avg_commission,
        COUNT(DISTINCT c.client_id) as total_clients,
        AVG(DATEDIFF(t.closing_date, al.listing_date)) as avg_days_to_close
    FROM Agent a
    LEFT JOIN Transaction t ON a.agent_id = t.agent_id
    LEFT JOIN AgentListing al ON t.listing_id = al.listing_id
    LEFT JOIN Client c ON (t.buyer_id = c.client_id OR t.seller_id = c.client_id)
    WHERE a.agent_id = p_agent_id;
END //

-- Update agent
CREATE PROCEDURE update_agent(
    IN p_agent_id INT,
    IN p_agent_name VARCHAR(255),
    IN p_agent_phone VARCHAR(15),
    IN p_agent_email VARCHAR(255),
    IN p_license_number VARCHAR(50),
    IN p_license_expiration DATE,
    IN p_commission_rate DECIMAL(5,2),
    IN p_broker_id INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Validate email if provided
    IF p_agent_email IS NOT NULL 
    AND p_agent_email NOT REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Invalid email format';
    END IF;

    -- Validate license expiration if provided
    IF p_license_expiration IS NOT NULL 
    AND p_license_expiration <= CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'License expiration date must be in the future';
    END IF;

    UPDATE Agent 
    SET 
        agent_name = COALESCE(p_agent_name, agent_name),
        agent_phone = COALESCE(p_agent_phone, agent_phone),
        agent_email = COALESCE(p_agent_email, agent_email),
        license_number = COALESCE(p_license_number, license_number),
        license_expiration = COALESCE(p_license_expiration, license_expiration),
        commission_rate = COALESCE(p_commission_rate, commission_rate),
        broker_id = COALESCE(p_broker_id, broker_id),
        last_modified = NOW()
    WHERE agent_id = p_agent_id;

    COMMIT;

    -- Return updated agent details
    CALL get_agent_details(p_agent_id);
END //

-- Delete agent
CREATE PROCEDURE delete_agent(
    IN p_agent_id INT
)
BEGIN
    DECLARE has_active_listings BOOLEAN;
    DECLARE has_active_transactions BOOLEAN;
    DECLARE user_id_to_delete INT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Check for active listings
    SELECT EXISTS (
        SELECT 1 FROM AgentListing 
        WHERE agent_id = p_agent_id 
        AND expiration_date > CURDATE()
    ) INTO has_active_listings;

    -- Check for active transactions
    SELECT EXISTS (
        SELECT 1 FROM Transaction 
        WHERE agent_id = p_agent_id
        AND closing_date > CURDATE()
    ) INTO has_active_transactions;

    IF has_active_listings THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot delete agent with active listings';
    END IF;

    IF has_active_transactions THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot delete agent with pending transactions';
    END IF;

    -- Get associated user ID if exists
    SELECT user_id INTO user_id_to_delete
    FROM User
    WHERE agent_id = p_agent_id;

    -- Delete related records
    DELETE FROM AgentShowing WHERE agent_id = p_agent_id;
    
    -- Delete user account if exists
    IF user_id_to_delete IS NOT NULL THEN
        DELETE FROM UserPermissions WHERE user_id = user_id_to_delete;
        DELETE FROM User WHERE user_id = user_id_to_delete;
    END IF;

    -- Delete agent
    DELETE FROM Agent WHERE agent_id = p_agent_id;

    COMMIT;
END //

-- Get agent performance metrics
CREATE PROCEDURE get_agent_performance(
    IN p_agent_id INT,
    IN p_start_date DATE,
    IN p_end_date DATE
)
BEGIN
    -- Get overall performance metrics
    SELECT 
        COUNT(DISTINCT t.transaction_id) as total_transactions,
        COUNT(DISTINCT CASE WHEN t.transaction_type = 'SALE' THEN t.transaction_id END) as total_sales,
        COUNT(DISTINCT CASE WHEN t.transaction_type = 'LEASE' THEN t.transaction_id END) as total_leases,
        COALESCE(SUM(t.amount), 0) as total_volume,
        COALESCE(SUM(t.commission_amount), 0) as total_commission,
        AVG(t.amount) as avg_transaction_value,
        COUNT(DISTINCT al.listing_id) as total_listings,
        COUNT(DISTINCT ash.showing_id) as total_showings,
        AVG(DATEDIFF(t.closing_date, al.listing_date)) as avg_days_to_close
    FROM Agent a
    LEFT JOIN Transaction t ON a.agent_id = t.agent_id
        AND t.transaction_date BETWEEN p_start_date AND p_end_date
    LEFT JOIN AgentListing al ON a.agent_id = al.agent_id
        AND al.listing_date BETWEEN p_start_date AND p_end_date
    LEFT JOIN AgentShowing ash ON a.agent_id = ash.agent_id
        AND ash.showing_date BETWEEN p_start_date AND p_end_date
    WHERE a.agent_id = p_agent_id;

    -- Get monthly performance breakdown
    SELECT 
        DATE_FORMAT(t.transaction_date, '%Y-%m') as month,
        COUNT(*) as transaction_count,
        SUM(t.amount) as total_volume,
        SUM(t.commission_amount) as total_commission,
        COUNT(DISTINCT CASE WHEN t.transaction_type = 'SALE' THEN t.transaction_id END) as sales_count,
        COUNT(DISTINCT CASE WHEN t.transaction_type = 'LEASE' THEN t.transaction_id END) as lease_count
    FROM Transaction t
    WHERE t.agent_id = p_agent_id
    AND t.transaction_date BETWEEN p_start_date AND p_end_date
    GROUP BY DATE_FORMAT(t.transaction_date, '%Y-%m')
    ORDER BY month;
END //

DELIMITER ;
