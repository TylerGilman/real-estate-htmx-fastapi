-- Drop the database if it exists and create a fresh one
DROP DATABASE IF EXISTS real_estate;
CREATE DATABASE real_estate;
USE real_estate;

-- Source schema (table definitions)
SOURCE sql/schema.sql;

-- Source all procedure files
SOURCE sql/procedures/auth_procedures.sql
SOURCE sql/procedures/agent_procedures.sql
SOURCE sql/procedures/property_procedures.sql
SOURCE sql/procedures/client_procedures.sql
SOURCE sql/procedures/listing_procedures.sql
SOURCE sql/procedures/transaction_procedures.sql
SOURCE sql/procedures/dashboard_procedures.sql

-- Insert initial data if needed
SOURCE sql/seed_data/roles.sql
SOURCE sql/seed_data/permissions.sql
SOURCE sql/seed_data/admin_user.sql
