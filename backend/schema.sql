-- Niramaya Health AI Database Initialization Script
-- Execute this script in PostgreSQL (psql or pgAdmin)

-- Create database if running from psql prompt:
-- CREATE DATABASE "projectH";
-- \c projectH;

CREATE TABLE IF NOT EXISTS account_tbl (
    account_id SERIAL PRIMARY KEY,
    family_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS member_tbl (
    member_id SERIAL PRIMARY KEY,
    account_id INT NOT NULL REFERENCES account_tbl(account_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    gender VARCHAR(50) NOT NULL,
    age INT NOT NULL,
    height VARCHAR(50),
    weight VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_history_tbl (
    history_id SERIAL PRIMARY KEY,
    account_id INT NOT NULL REFERENCES account_tbl(account_id) ON DELETE CASCADE,
    member_id INT NOT NULL REFERENCES member_tbl(member_id) ON DELETE CASCADE,
    user_input TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    model VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_tbl (
    admin_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) DEFAULT 'admin' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_tokens_tbl (
    token_id SERIAL PRIMARY KEY,
    admin_id INT NOT NULL REFERENCES admin_tbl(admin_id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS health_content_tbl (
    content_id SERIAL PRIMARY KEY,
    content_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    content TEXT NOT NULL,
    author_or_source VARCHAR(255),
    external_link VARCHAR(500),
    image_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'published' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


