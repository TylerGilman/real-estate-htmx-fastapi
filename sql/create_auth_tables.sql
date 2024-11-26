-- sql/create_auth_tables.sql
CREATE TABLE IF NOT EXISTS UserRole (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS User (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    agent_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES UserRole(role_id),
    FOREIGN KEY (agent_id) REFERENCES Agent(agent_id) ON DELETE CASCADE
);

-- Insert initial roles if they don't exist
INSERT IGNORE INTO UserRole (role_name) VALUES ('admin'), ('agent');
