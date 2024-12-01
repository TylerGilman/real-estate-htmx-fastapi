-- Drop the database if it exists and create a fresh one
DROP DATABASE IF EXISTS real_estate;
CREATE DATABASE real_estate;
USE real_estate;

-- Source schema (table definitions)
SOURCE schema.sql;

-- Source all procedure files
SOURCE procedures/auth_procedures.sql
SOURCE procedures/agent_procedures.sql
SOURCE procedures/property_procedures.sql
SOURCE procedures/client_procedures.sql
SOURCE procedures/listing_procedures.sql
SOURCE procedures/transaction_procedures.sql
SOURCE procedures/dashboard_procedures.sql

-- Insert initial data if needed
SOURCE seed_data/roles.sql
SOURCE seed_data/permissions.sql
SOURCE seed_data/admin_user.sql
