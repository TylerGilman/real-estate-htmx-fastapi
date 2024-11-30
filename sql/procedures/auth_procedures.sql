DELIMITER //

-- Create or get admin role
CREATE PROCEDURE get_or_create_admin_role()
BEGIN
    DECLARE admin_role_id INT;
    
    SELECT role_id INTO admin_role_id
    FROM UserRole
    WHERE role_name = 'admin'
    LIMIT 1;
    
    IF admin_role_id IS NULL THEN
        INSERT INTO UserRole (role_name)
        VALUES ('admin');
        
        SET admin_role_id = LAST_INSERT_ID();
    END IF;
    
    SELECT role_id, role_name
    FROM UserRole
    WHERE role_id = admin_role_id;
END //

-- Validate user session
CREATE PROCEDURE validate_session(
    IN p_session_id VARCHAR(100),
    IN p_ip_address VARCHAR(45)
)
BEGIN
    DECLARE is_valid BOOLEAN;
    
    SELECT 
        EXISTS (
            SELECT 1
            FROM Sessions s
            WHERE s.session_id = p_session_id
            AND s.ip_address = p_ip_address
            AND s.expires > NOW()
            AND s.is_active = TRUE
        ) INTO is_valid;

    SELECT 
        is_valid as is_valid,
        CASE 
            WHEN is_valid THEN 'Valid session'
            ELSE 'Invalid or expired session'
        END as message;
END //

-- Check user permissions
CREATE PROCEDURE check_user_permission(
    IN p_user_id INT,
    IN p_permission VARCHAR(50)
)
BEGIN
    SELECT 
        EXISTS (
            SELECT 1
            FROM UserPermissions up
            JOIN Permissions p ON up.permission_id = p.permission_id
            WHERE up.user_id = p_user_id
            AND p.permission_name = p_permission
        ) OR EXISTS (
            SELECT 1
            FROM User u
            JOIN UserRole ur ON u.role_id = ur.role_id
            JOIN RolePermissions rp ON ur.role_id = rp.role_id
            JOIN Permissions p ON rp.permission_id = p.permission_id
            WHERE u.user_id = p_user_id
            AND p.permission_name = p_permission
        ) as has_permission;
END //

-- Get user by username with role and details
CREATE PROCEDURE get_user_by_username(
    IN p_username VARCHAR(100)
)
BEGIN
    SELECT 
        u.user_id,
        u.username,
        u.password_hash,
        u.role_id,
        u.agent_id,
        u.last_login,
        u.created_at,
        ur.role_name,
        a.agent_name,
        a.agent_phone,
        a.agent_email,
        a.license_number,
        a.license_expiration
    FROM User u
    JOIN UserRole ur ON u.role_id = ur.role_id
    LEFT JOIN Agent a ON u.agent_id = a.agent_id
    WHERE u.username = p_username;
END //

-- Create admin user
CREATE PROCEDURE create_admin_user(
    IN p_username VARCHAR(100),
    IN p_password_hash VARCHAR(255)
)
BEGIN
    DECLARE admin_role_id INT;
    DECLARE new_user_id INT;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    CALL get_or_create_admin_role();
    
    SELECT role_id INTO admin_role_id
    FROM UserRole
    WHERE role_name = 'admin'
    LIMIT 1;
    
    IF EXISTS (SELECT 1 FROM User WHERE username = p_username) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Username already exists';
    END IF;
    
    INSERT INTO User (
        username, 
        password_hash, 
        role_id,
        created_at,
        last_modified
    ) VALUES (
        p_username,
        p_password_hash,
        admin_role_id,
        NOW(),
        NOW()
    );
    
    COMMIT;
    
    SELECT 
        u.user_id,
        u.username,
        ur.role_name,
        u.created_at
    FROM User u
    JOIN UserRole ur ON u.role_id = ur.role_id
    WHERE u.username = p_username;
END //

-- Create regular user
CREATE PROCEDURE create_user(
    IN p_username VARCHAR(100),
    IN p_password_hash VARCHAR(255),
    IN p_role_name VARCHAR(50),
    IN p_agent_id INT
)
BEGIN
    DECLARE v_role_id INT;
    
    SELECT role_id INTO v_role_id
    FROM UserRole
    WHERE role_name = p_role_name;
    
    IF v_role_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Invalid role name';
    END IF;
    
    INSERT INTO User (
        username,
        password_hash,
        role_id,
        agent_id,
        created_at,
        last_modified
    ) VALUES (
        p_username,
        p_password_hash,
        v_role_id,
        p_agent_id,
        NOW(),
        NOW()
    );
    
    SELECT LAST_INSERT_ID() as user_id;
END //

-- Log user login
CREATE PROCEDURE log_user_login(
    IN p_user_id INT,
    IN p_ip_address VARCHAR(45)
)
BEGIN
    UPDATE User 
    SET 
        last_login = NOW(),
        last_ip_address = p_ip_address
    WHERE user_id = p_user_id;
    
    INSERT INTO LoginLog (
        user_id,
        ip_address,
        login_time
    ) VALUES (
        p_user_id,
        p_ip_address,
        NOW()
    );
END //

DELIMITER ;
