DELIMITER //

CREATE PROCEDURE get_all_properties_with_images()
BEGIN
    -- Get all properties
    SELECT 
        p.*,
        GROUP_CONCAT(
            JSON_OBJECT(
                'image_id', pi.image_id,
                'file_path', pi.file_path,
                'is_primary', pi.is_primary
            )
        ) as images
    FROM Property p
    LEFT JOIN PropertyImages pi ON p.property_id = pi.property_id
    GROUP BY p.property_id;
END //

CREATE PROCEDURE add_property_image(
    IN p_property_id INT,
    IN p_file_path VARCHAR(255),
    IN p_is_primary BOOLEAN
)
BEGIN
    -- If this is marked as primary, unset any existing primary image
    IF p_is_primary THEN
        UPDATE PropertyImages 
        SET is_primary = FALSE 
        WHERE property_id = p_property_id AND is_primary = TRUE;
    END IF;
    
    INSERT INTO PropertyImages (
        property_id,
        file_path,
        is_primary
    ) VALUES (
        p_property_id,
        p_file_path,
        p_is_primary
    );
END //

CREATE PROCEDURE get_property_images(
    IN p_property_id INT
)
BEGIN
    SELECT 
        image_id,
        file_path,
        is_primary,
        uploaded_at
    FROM PropertyImages
    WHERE property_id = p_property_id
    ORDER BY is_primary DESC, uploaded_at DESC;
END //

CREATE PROCEDURE set_primary_image(
    IN p_image_id INT
)
BEGIN
    DECLARE v_property_id INT;
    
    -- Get property_id for the image
    SELECT property_id INTO v_property_id
    FROM PropertyImages
    WHERE image_id = p_image_id;
    
    -- Update all images for the property
    UPDATE PropertyImages
    SET is_primary = FALSE
    WHERE property_id = v_property_id;
    
    -- Set the selected image as primary
    UPDATE PropertyImages
    SET is_primary = TRUE
    WHERE image_id = p_image_id;
END //

CREATE PROCEDURE delete_property_image(
    IN p_image_id INT
)
BEGIN
    DELETE FROM PropertyImages
    WHERE image_id = p_image_id;
END //

DELIMITER ;
