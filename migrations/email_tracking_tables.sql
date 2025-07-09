-- Email Tracking Tables for BITTEN Press Pass Campaign
-- Tracks sent emails, opens, clicks, and campaign performance

-- Email log table
CREATE TABLE IF NOT EXISTS email_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    email_address TEXT NOT NULL,
    template TEXT NOT NULL,
    subject TEXT NOT NULL,
    campaign TEXT DEFAULT 'press_pass',
    campaign_day INTEGER,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    bounced BOOLEAN DEFAULT FALSE,
    unsubscribed BOOLEAN DEFAULT FALSE,
    tracking_id TEXT UNIQUE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Email clicks tracking
CREATE TABLE IF NOT EXISTS email_clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_log_id INTEGER NOT NULL,
    link_url TEXT NOT NULL,
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY (email_log_id) REFERENCES email_log(id)
);

-- Email campaign stats
CREATE TABLE IF NOT EXISTS email_campaign_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign TEXT NOT NULL,
    date DATE NOT NULL,
    total_sent INTEGER DEFAULT 0,
    total_opened INTEGER DEFAULT 0,
    total_clicked INTEGER DEFAULT 0,
    total_bounced INTEGER DEFAULT 0,
    total_unsubscribed INTEGER DEFAULT 0,
    unique_opens INTEGER DEFAULT 0,
    unique_clicks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(campaign, date)
);

-- Email queue for scheduled sends
CREATE TABLE IF NOT EXISTS email_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    email_address TEXT NOT NULL,
    template TEXT NOT NULL,
    subject TEXT NOT NULL,
    template_data TEXT, -- JSON data
    scheduled_for TIMESTAMP NOT NULL,
    priority INTEGER DEFAULT 5,
    status TEXT DEFAULT 'pending', -- pending, sent, failed
    attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP,
    sent_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Email preferences
CREATE TABLE IF NOT EXISTS email_preferences (
    user_id INTEGER PRIMARY KEY,
    opt_in_marketing BOOLEAN DEFAULT TRUE,
    opt_in_updates BOOLEAN DEFAULT TRUE,
    opt_in_press_pass BOOLEAN DEFAULT TRUE,
    email_frequency TEXT DEFAULT 'normal', -- normal, digest, minimal
    unsubscribed BOOLEAN DEFAULT FALSE,
    unsubscribed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX idx_email_log_user_id ON email_log(user_id);
CREATE INDEX idx_email_log_sent_at ON email_log(sent_at);
CREATE INDEX idx_email_log_tracking_id ON email_log(tracking_id);
CREATE INDEX idx_email_queue_scheduled ON email_queue(scheduled_for, status);
CREATE INDEX idx_email_queue_user_id ON email_queue(user_id);

-- Views for analytics
CREATE VIEW IF NOT EXISTS email_campaign_performance AS
SELECT 
    el.campaign,
    el.template,
    COUNT(*) as total_sent,
    SUM(CASE WHEN el.opened_at IS NOT NULL THEN 1 ELSE 0 END) as total_opened,
    SUM(CASE WHEN el.clicked_at IS NOT NULL THEN 1 ELSE 0 END) as total_clicked,
    ROUND(100.0 * SUM(CASE WHEN el.opened_at IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as open_rate,
    ROUND(100.0 * SUM(CASE WHEN el.clicked_at IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as click_rate
FROM email_log el
GROUP BY el.campaign, el.template;

CREATE VIEW IF NOT EXISTS user_email_engagement AS
SELECT 
    u.id as user_id,
    u.username,
    u.email,
    COUNT(el.id) as total_emails_received,
    SUM(CASE WHEN el.opened_at IS NOT NULL THEN 1 ELSE 0 END) as emails_opened,
    SUM(CASE WHEN el.clicked_at IS NOT NULL THEN 1 ELSE 0 END) as emails_clicked,
    MAX(el.sent_at) as last_email_sent,
    MAX(el.opened_at) as last_email_opened
FROM users u
LEFT JOIN email_log el ON u.id = el.user_id
GROUP BY u.id;