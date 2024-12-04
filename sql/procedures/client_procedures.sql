DELIMITER //

-- Create Client
DROP PROCEDURE IF EXISTS create_client;
CREATE PROCEDURE create_client(
    IN p_client_name VARCHAR(255),
    IN p_SSN VARCHAR(15),
    IN p_mailing_address VARCHAR(255),
    IN p_client_phone VARCHAR(15),
    IN p_client_email VARCHAR(255)
)
BEGIN
    INSERT INTO Client (client_name, SSN, mailing_address, client_phone, client_email)
    VALUES (p_client_name, p_SSN, p_mailing_address, p_client_phone, p_client_email);
END //

-- Update Client
DROP PROCEDURE IF EXISTS update_client;
CREATE PROCEDURE update_client(
    IN p_client_id INT,
    IN p_client_name VARCHAR(255),
    IN p_client_phone VARCHAR(15),
    IN p_client_email VARCHAR(255),
    IN p_mailing_address VARCHAR(255)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    UPDATE Client
    SET 
        client_name = COALESCE(p_client_name, client_name),
        client_phone = COALESCE(p_client_phone, client_phone),
        client_email = COALESCE(p_client_email, client_email),
        mailing_address = COALESCE(p_mailing_address, mailing_address),
        last_modified = NOW()
    WHERE client_id = p_client_id;

    COMMIT;
END //

-- Delete Client
DROP PROCEDURE IF EXISTS delete_client;
CREATE PROCEDURE delete_client(
    IN p_client_id INT
)
BEGIN
    DELETE FROM Client
    WHERE client_id = p_client_id;
END //

-- Get All Clients
DROP PROCEDURE IF EXISTS get_all_clients;
CREATE PROCEDURE get_all_clients()
BEGIN
    SELECT 
        client_id,
        client_name,
        client_phone,
        client_email,
        mailing_address
    FROM Client
    ORDER BY client_name ASC;
END //

-- Get Client Details
DROP PROCEDURE IF EXISTS get_client_details;
CREATE PROCEDURE get_client_details(
    IN p_client_id INT
)
BEGIN
    SELECT 
        client_id,
        client_name,
        client_phone,
        client_email,
        mailing_address,
        SSN,
        created_at
    FROM Client
    WHERE client_id = p_client_id;
END //

-- Search Clients
DROP PROCEDURE IF EXISTS search_clients;
CREATE PROCEDURE search_clients(
    IN p_search_query VARCHAR(255)
)
BEGIN
    SELECT 
        client_id,
        client_name,
        client_phone,
        client_email,
        mailing_address,
        created_at,
        last_modified
    FROM Client
    WHERE client_name LIKE CONCAT('%', p_search_query, '%')
       OR client_phone LIKE CONCAT('%', p_search_query, '%')
       OR client_email LIKE CONCAT('%', p_search_query, '%')
    ORDER BY client_name ASC;
END //

DELIMITER ;
