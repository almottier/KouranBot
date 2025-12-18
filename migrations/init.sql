-- KouranBot Database Initialization Script

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    language VARCHAR(2) DEFAULT 'fr',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create districts table
CREATE TABLE IF NOT EXISTS districts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create localities table
CREATE TABLE IF NOT EXISTS localities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    district_id INTEGER REFERENCES districts(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, district_id)
);

-- Create subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    locality_id INTEGER REFERENCES localities(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, locality_id)
);

-- Create outages table
CREATE TABLE IF NOT EXISTS outages (
    id VARCHAR(255) PRIMARY KEY,
    locality VARCHAR(255) NOT NULL,
    district VARCHAR(255) NOT NULL,
    streets TEXT,
    date_description TEXT,
    from_time TIMESTAMP NOT NULL,
    to_time TIMESTAMP NOT NULL,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create notifications_sent table
CREATE TABLE IF NOT EXISTS notifications_sent (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    outage_id VARCHAR(255) REFERENCES outages(id) ON DELETE CASCADE,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, outage_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_localities_district_id ON localities(district_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_locality_id ON subscriptions(locality_id);
CREATE INDEX IF NOT EXISTS idx_outages_locality ON outages(locality);
CREATE INDEX IF NOT EXISTS idx_outages_district ON outages(district);
CREATE INDEX IF NOT EXISTS idx_notifications_user_outage ON notifications_sent(user_id, outage_id);
