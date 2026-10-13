-- SETMS PostgreSQL initialization script
-- Runs once when the Docker postgres container is first created

-- Extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
