-- BITTEN Psychological Warfare Database Schema
-- Tracks user transformation from broken trader to tactical weapon

-- Core psychological profile
CREATE TABLE user_psychology (
    user_id VARCHAR(50) PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    
    -- Trauma assessment
    trauma_type VARCHAR(50), -- blown_account, revenge_trade, borrowed_money, loop, scammed
    trauma_severity INTEGER DEFAULT 5, -- 1-10 scale
    trauma_confession_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Emotional state tracking
    emotions_replaced JSONB DEFAULT '{}', -- {"fear": 0.8, "greed": 0.6, "revenge": 0.9}
    emotion_incidents JSONB DEFAULT '[]', -- Track emotional breaks
    last_tilt_event TIMESTAMP,
    tilt_recovery_time INTEGER, -- seconds to recover
    
    -- Tactical identity
    tactical_identity VARCHAR(50), -- LONE_WOLF, SQUAD_LEADER, SNIPER, ASSAULT
    identity_locked_date TIMESTAMP,
    identity_strength DECIMAL(3,2) DEFAULT 0.0, -- 0-1 confidence in identity
    
    -- Norman story progress
    story_chapter INTEGER DEFAULT 0,
    story_unlocks JSONB DEFAULT '[]', -- ["chapter_1_loss", "bit_origin", "dad_video"]
    last_story_unlock TIMESTAMP,
    
    -- Bit relationship
    bit_trust_score INTEGER DEFAULT 0, -- -100 to 100
    bit_interactions JSONB DEFAULT '[]',
    bit_warnings_heeded INTEGER DEFAULT 0,
    bit_warnings_ignored INTEGER DEFAULT 0,
    
    -- Psychological state
    dissociation_level DECIMAL(3,2) DEFAULT 0.0, -- 0-1, how deep in the "game"
    reality_anchor_score DECIMAL(3,2) DEFAULT 1.0, -- 1-0, connection to real consequences
    addiction_risk_score DECIMAL(3,2) DEFAULT 0.0, -- 0-1, gambling addiction indicators
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Emotion replacement tracking
CREATE TABLE emotion_replacements (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES user_psychology(user_id),
    
    -- Original emotion
    original_emotion VARCHAR(50), -- fear, greed, revenge, hope, panic, fomo
    emotion_trigger VARCHAR(255), -- what caused it
    emotion_intensity DECIMAL(3,2), -- 0-1
    
    -- Tactical replacement
    replacement_protocol VARCHAR(50), -- retreat, objective, cooldown, evacuation
    protocol_executed BOOLEAN DEFAULT FALSE,
    execution_time INTEGER, -- milliseconds to execute
    
    -- Outcome
    trade_avoided BOOLEAN DEFAULT FALSE,
    loss_prevented DECIMAL(10,2),
    lesson_learned TEXT,
    
    -- Metadata
    market_conditions JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hidden education progress
CREATE TABLE stealth_education (
    user_id VARCHAR(50) REFERENCES user_psychology(user_id),
    concept_id VARCHAR(100),
    
    -- Learning tracking
    concept_name VARCHAR(255),
    concept_category VARCHAR(50), -- basics, risk, analysis, psychology, institutional
    first_exposure TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exposure_count INTEGER DEFAULT 1,
    
    -- Mastery assessment
    understanding_level INTEGER DEFAULT 0, -- 0-100
    practical_application_count INTEGER DEFAULT 0,
    successful_applications INTEGER DEFAULT 0,
    
    -- Discovery method
    learned_through VARCHAR(100), -- mission_name, loss_event, personality_hint
    discovery_was_organic BOOLEAN DEFAULT TRUE, -- vs forced tutorial
    aha_moment_logged BOOLEAN DEFAULT FALSE,
    
    -- Retention
    last_application TIMESTAMP,
    retention_score DECIMAL(3,2) DEFAULT 0.0, -- 0-1
    
    PRIMARY KEY (user_id, concept_id)
);

-- Mission progress with psychological hooks
CREATE TABLE mission_progress (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES user_psychology(user_id),
    mission_id VARCHAR(100),
    
    -- Mission details
    mission_name VARCHAR(255),
    mission_tier INTEGER, -- 1-6 difficulty
    psychological_goal VARCHAR(255), -- "Replace fear with protocol"
    educational_goal VARCHAR(255), -- Hidden: "Learn support/resistance"
    
    -- Progress tracking
    status VARCHAR(50) DEFAULT 'assigned', -- assigned, in_progress, completed, failed
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Psychological impact
    emotion_replaced VARCHAR(50),
    discipline_score DECIMAL(3,2), -- 0-1, how well they followed protocol
    impulse_resisted_count INTEGER DEFAULT 0,
    
    -- Performance
    trades_required INTEGER,
    trades_completed INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    profit_loss DECIMAL(10,2),
    
    -- Bonus objectives
    bonus_objectives JSONB DEFAULT '[]',
    bonuses_completed INTEGER DEFAULT 0
);

-- Squad dynamics and trauma bonding
CREATE TABLE squad_psychology (
    squad_id VARCHAR(100) PRIMARY KEY,
    squad_name VARCHAR(255),
    
    -- Formation
    formed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    formation_trigger VARCHAR(100), -- shared_loss, referral, random_assignment
    
    -- Psychological metrics
    trauma_bond_strength DECIMAL(3,2) DEFAULT 0.0, -- 0-1
    collective_discipline_score DECIMAL(3,2) DEFAULT 0.5,
    group_identity_strength DECIMAL(3,2) DEFAULT 0.0,
    
    -- Shared experiences
    collective_wins INTEGER DEFAULT 0,
    collective_losses INTEGER DEFAULT 0,
    members_saved_from_tilt INTEGER DEFAULT 0,
    group_confessions JSONB DEFAULT '[]', -- Shared trauma stories
    
    -- Teaching cycles
    peer_lessons_shared INTEGER DEFAULT 0,
    knowledge_transfer_score DECIMAL(3,2) DEFAULT 0.0,
    veteran_guidance_events INTEGER DEFAULT 0,
    
    -- Squad health
    toxicity_score DECIMAL(3,2) DEFAULT 0.0, -- 0-1, negative behavior
    support_score DECIMAL(3,2) DEFAULT 0.5, -- 0-1, positive reinforcement
    last_activity TIMESTAMP
);

-- Individual squad membership
CREATE TABLE squad_members (
    user_id VARCHAR(50) REFERENCES user_psychology(user_id),
    squad_id VARCHAR(100) REFERENCES squad_psychology(squad_id),
    
    -- Role and status
    role VARCHAR(50) DEFAULT 'soldier', -- soldier, veteran, commander
    joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    contribution_score DECIMAL(3,2) DEFAULT 0.0,
    
    -- Psychological impact
    isolation_before_squad DECIMAL(3,2), -- 0-1, how alone they felt
    belonging_after_squad DECIMAL(3,2), -- 0-1, connection feeling
    peer_support_given INTEGER DEFAULT 0,
    peer_support_received INTEGER DEFAULT 0,
    
    PRIMARY KEY (user_id, squad_id)
);

-- Personality fragment interactions
CREATE TABLE personality_interactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES user_psychology(user_id),
    
    -- Interaction details
    personality VARCHAR(50), -- DRILL, DOC, NEXUS, OVERWATCH, ATHENA, BIT
    trigger_event VARCHAR(100), -- impulsive_trade, big_loss, overleveraged
    message_sent TEXT,
    
    -- User response
    message_heeded BOOLEAN,
    action_taken VARCHAR(100),
    emotion_before VARCHAR(50),
    emotion_after VARCHAR(50),
    
    -- Impact measurement
    loss_prevented DECIMAL(10,2),
    discipline_reinforced BOOLEAN DEFAULT FALSE,
    lesson_internalized BOOLEAN DEFAULT FALSE,
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tilt detection and intervention
CREATE TABLE tilt_events (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES user_psychology(user_id),
    
    -- Tilt detection
    tilt_type VARCHAR(50), -- revenge, overleveraging, chasing, panic
    tilt_severity DECIMAL(3,2), -- 0-1
    triggers JSONB, -- What caused it
    
    -- Intervention
    intervention_type VARCHAR(100), -- lockout, personality_message, squad_alert
    intervention_accepted BOOLEAN,
    
    -- Recovery
    recovery_time_seconds INTEGER,
    recovery_method VARCHAR(100),
    damage_prevented DECIMAL(10,2),
    
    -- Learning
    post_tilt_reflection TEXT,
    pattern_recognized BOOLEAN DEFAULT FALSE,
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Achievement unlocks with psychological significance
CREATE TABLE psychological_achievements (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES user_psychology(user_id),
    
    -- Achievement details
    achievement_id VARCHAR(100),
    achievement_name VARCHAR(255),
    achievement_tier VARCHAR(50), -- bronze, silver, gold, platinum, diamond
    
    -- Psychological significance
    psychological_milestone VARCHAR(255), -- "First time resisting revenge trade"
    emotion_conquered VARCHAR(50),
    behavioral_change_demonstrated TEXT,
    
    -- Unlock details
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unlock_method VARCHAR(100), -- organic, forced, squad_assisted
    celebration_viewed BOOLEAN DEFAULT FALSE,
    
    -- Social proof
    shared_with_squad BOOLEAN DEFAULT FALSE,
    inspired_others_count INTEGER DEFAULT 0
);

-- Daily psychological metrics
CREATE TABLE daily_psych_metrics (
    user_id VARCHAR(50) REFERENCES user_psychology(user_id),
    date DATE,
    
    -- Emotional state
    emotional_stability_score DECIMAL(3,2), -- 0-1
    impulse_control_score DECIMAL(3,2), -- 0-1
    protocol_adherence_score DECIMAL(3,2), -- 0-1
    
    -- Trading behavior
    trades_attempted INTEGER DEFAULT 0,
    trades_executed INTEGER DEFAULT 0,
    emotional_trades_prevented INTEGER DEFAULT 0,
    
    -- Psychological progress
    dissociation_depth DECIMAL(3,2), -- How deep in game mindset
    tactical_thinking_score DECIMAL(3,2), -- 0-1
    
    -- Risk indicators
    tilt_events INTEGER DEFAULT 0,
    near_tilt_events INTEGER DEFAULT 0,
    interventions_needed INTEGER DEFAULT 0,
    
    -- Education
    concepts_discovered INTEGER DEFAULT 0,
    concepts_applied INTEGER DEFAULT 0,
    
    PRIMARY KEY (user_id, date)
);

-- Indexes for performance
CREATE INDEX idx_psychology_trauma ON user_psychology(trauma_type);
CREATE INDEX idx_psychology_identity ON user_psychology(tactical_identity);
CREATE INDEX idx_emotion_timestamp ON emotion_replacements(timestamp);
CREATE INDEX idx_education_concept ON stealth_education(concept_category);
CREATE INDEX idx_mission_status ON mission_progress(status);
CREATE INDEX idx_squad_activity ON squad_psychology(last_activity);
CREATE INDEX idx_personality_timestamp ON personality_interactions(timestamp);
CREATE INDEX idx_tilt_user_time ON tilt_events(user_id, timestamp);
CREATE INDEX idx_achievement_tier ON psychological_achievements(achievement_tier);
CREATE INDEX idx_daily_metrics_date ON daily_psych_metrics(date);

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_psychology_updated_at 
    BEFORE UPDATE ON user_psychology 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Views for psychological analysis
CREATE VIEW user_transformation_progress AS
SELECT 
    up.user_id,
    up.trauma_type,
    up.tactical_identity,
    up.dissociation_level,
    COUNT(DISTINCT er.original_emotion) as emotions_replaced_count,
    COUNT(DISTINCT se.concept_id) as concepts_learned,
    COUNT(DISTINCT mp.mission_id) as missions_completed,
    AVG(dpm.emotional_stability_score) as avg_emotional_stability,
    MAX(pa.achievement_tier) as highest_achievement
FROM user_psychology up
LEFT JOIN emotion_replacements er ON up.user_id = er.user_id
LEFT JOIN stealth_education se ON up.user_id = se.user_id
LEFT JOIN mission_progress mp ON up.user_id = mp.user_id AND mp.status = 'completed'
LEFT JOIN daily_psych_metrics dpm ON up.user_id = dpm.user_id
LEFT JOIN psychological_achievements pa ON up.user_id = pa.user_id
GROUP BY up.user_id, up.trauma_type, up.tactical_identity, up.dissociation_level;

-- View for squad health
CREATE VIEW squad_health_metrics AS
SELECT 
    sp.squad_id,
    sp.squad_name,
    sp.trauma_bond_strength,
    sp.collective_discipline_score,
    COUNT(DISTINCT sm.user_id) as member_count,
    AVG(up.bit_trust_score) as avg_bit_trust,
    SUM(sp.members_saved_from_tilt) as total_saves,
    sp.toxicity_score,
    sp.support_score
FROM squad_psychology sp
LEFT JOIN squad_members sm ON sp.squad_id = sm.squad_id
LEFT JOIN user_psychology up ON sm.user_id = up.user_id
GROUP BY sp.squad_id, sp.squad_name, sp.trauma_bond_strength, 
         sp.collective_discipline_score, sp.members_saved_from_tilt,
         sp.toxicity_score, sp.support_score;