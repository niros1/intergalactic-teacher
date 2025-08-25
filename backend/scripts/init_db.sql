-- Initialize database for Intergalactic Teacher
-- This script runs when the PostgreSQL container starts

-- Create the database if it doesn't exist
SELECT 'CREATE DATABASE intergalactic_teacher'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'intergalactic_teacher');

-- Create test database
SELECT 'CREATE DATABASE intergalactic_teacher_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'intergalactic_teacher_test');

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create user if doesn't exist (for development)
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'intergalactic') THEN

      CREATE ROLE intergalactic LOGIN PASSWORD 'password';
      GRANT ALL PRIVILEGES ON DATABASE intergalactic_teacher TO intergalactic;
      GRANT ALL PRIVILEGES ON DATABASE intergalactic_teacher_test TO intergalactic;
   END IF;
END
$do$;