
DELIMITER //

-- Drop procedure if it exists

DROP PROCEDURE IF EXISTS get_admin_dashboard_stats;
CREATE PROCEDURE get_admin_dashboard_stats()
BEGIN
    SELECT 
        (SELECT COUNT(*) FROM Property) AS total_properties,
        (SELECT COUNT(*) FROM Transaction) AS total_transactions,
        (SELECT COUNT(*) FROM Agent) AS total_agents;
END //


-- Drop procedure if it exists
DROP PROCEDURE IF EXISTS get_recent_transactions;
CREATE PROCEDURE get_recent_transactions()
BEGIN
    SELECT 
        t.transaction_id,
        t.property_id,
        p.property_address,
        t.amount,
        t.transaction_date,
        a.agent_name AS agent_involved
    FROM Transaction t
    JOIN Property p ON t.property_id = p.property_id
    LEFT JOIN Agent a ON t.agent_id = a.agent_id
    ORDER BY t.transaction_date DESC
    LIMIT 10;
END //

-- Drop procedure if it exists
DROP PROCEDURE IF EXISTS get_top_agents;
CREATE PROCEDURE get_top_agents()
BEGIN
    SELECT 
        a.agent_id,
        a.agent_name,
        COUNT(t.transaction_id) AS total_transactions,
        SUM(t.amount) AS total_sales
    FROM Agent a
    JOIN Transaction t ON a.agent_id = t.agent_id
    GROUP BY a.agent_id, a.agent_name
    ORDER BY total_sales DESC
    LIMIT 5;
END //

-- Drop procedure if it exists
DROP PROCEDURE IF EXISTS get_property_status_breakdown;
CREATE PROCEDURE get_property_status_breakdown()
BEGIN
    SELECT 
        status,
        COUNT(*) AS total_properties
    FROM Properties
    GROUP BY status;
END //

-- Drop procedure if it exists
DROP PROCEDURE IF EXISTS get_monthly_transactions;
CREATE PROCEDURE get_monthly_transactions()
BEGIN
    SELECT 
        DATE_FORMAT(t.transaction_date, '%Y-%m') AS transaction_month,
        COUNT(*) AS total_transactions,
        SUM(t.amount) AS total_sales
    FROM Transaction t
    GROUP BY transaction_month
    ORDER BY transaction_month DESC
    LIMIT 12;
END //

DELIMITER ;
