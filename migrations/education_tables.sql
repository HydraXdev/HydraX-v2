-- 🎯 BITTEN Education System Database Migration
-- Version: 1.0
-- Created: 2025-01-07
-- Description: Comprehensive education system tables for mission progress, video tracking,
--              squad system, mentorship, study groups, achievements, and analytics

-- ==========================================
-- EDUCATION MISSIONS & PROGRESS
-- ==========================================

-- Education missions definition
CREATE TABLE education_missions (
    mission_id BIGSERIAL PRIMARY KEY,
    
    -- Mission details
    code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- onboarding, trading_basics, advanced_strategies, psychological
    difficulty VARCHAR(50) NOT NULL, -- beginner, intermediate, advanced, expert
    
    -- Mission structure
    objectives JSONB NOT NULL, -- [{id: 1, task: "Watch intro video", required: true, xp: 100}]
    prerequisites JSONB DEFAULT '[]'::jsonb, -- [mission_code1, mission_code2]
    estimated_duration_minutes INTEGER,
    
    -- Rewards
    xp_reward INTEGER NOT NULL DEFAULT 0,
    completion_bonus_xp INTEGER DEFAULT 0,
    unlocks JSONB DEFAULT '[]'::jsonb, -- Features, missions, or content unlocked
    
    -- Display
    icon_url VARCHAR(500),
    banner_url VARCHAR(500),
    display_order INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    tier_requirement VARCHAR(50), -- Minimum tier required
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_education_missions_category (category),
    INDEX idx_education_missions_difficulty (difficulty),
    INDEX idx_education_missions_active (is_active)
);

-- User mission progress tracking
CREATE TABLE user_mission_progress (
    progress_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    mission_id BIGINT NOT NULL REFERENCES education_missions(mission_id),
    
    -- Progress tracking
    status VARCHAR(50) NOT NULL DEFAULT 'not_started', -- not_started, in_progress, completed, abandoned
    objectives_completed JSONB DEFAULT '[]'::jsonb, -- [1, 3, 5] - IDs of completed objectives
    current_objective_id INTEGER,
    progress_percent INTEGER DEFAULT 0,
    
    -- Time tracking
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    last_activity_at TIMESTAMP WITH TIME ZONE,
    time_spent_seconds INTEGER DEFAULT 0,
    
    -- Performance
    attempts INTEGER DEFAULT 0,
    quiz_scores JSONB DEFAULT '[]'::jsonb, -- [{attempt: 1, score: 85, date: "2025-01-07"}]
    best_quiz_score INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, mission_id),
    INDEX idx_user_mission_progress_user (user_id),
    INDEX idx_user_mission_progress_status (status),
    INDEX idx_user_mission_progress_activity (last_activity_at DESC)
);

-- ==========================================
-- VIDEO CONTENT & PROGRESS
-- ==========================================

-- Educational video content
CREATE TABLE education_videos (
    video_id BIGSERIAL PRIMARY KEY,
    
    -- Video details
    code VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    tags JSONB DEFAULT '[]'::jsonb,
    
    -- Video data
    video_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    duration_seconds INTEGER NOT NULL,
    
    -- Checkpoints for progress tracking
    checkpoints JSONB DEFAULT '[]'::jsonb, -- [{time: 30, id: "intro_complete", xp: 50}]
    
    -- Associated content
    mission_id BIGINT REFERENCES education_missions(mission_id),
    quiz_id BIGINT, -- Reference to quiz if video has one
    
    -- Requirements
    tier_requirement VARCHAR(50),
    prerequisite_videos JSONB DEFAULT '[]'::jsonb,
    
    -- Metadata
    instructor_name VARCHAR(255),
    difficulty_level VARCHAR(50),
    view_count INTEGER DEFAULT 0,
    average_rating DECIMAL(3,2),
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_education_videos_category (category),
    INDEX idx_education_videos_mission (mission_id)
);

-- User video progress
CREATE TABLE user_video_progress (
    progress_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    video_id BIGINT NOT NULL REFERENCES education_videos(video_id),
    
    -- Progress tracking
    watch_percent INTEGER DEFAULT 0,
    last_position_seconds INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    
    -- Checkpoint tracking
    checkpoints_reached JSONB DEFAULT '[]'::jsonb, -- ["intro_complete", "midpoint"]
    
    -- Engagement metrics
    total_watch_time_seconds INTEGER DEFAULT 0,
    watch_sessions INTEGER DEFAULT 0,
    
    -- Quiz results if applicable
    quiz_attempted BOOLEAN DEFAULT FALSE,
    quiz_score INTEGER,
    quiz_attempts INTEGER DEFAULT 0,
    
    -- Timestamps
    first_watched_at TIMESTAMP WITH TIME ZONE,
    last_watched_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, video_id),
    INDEX idx_user_video_progress_user (user_id),
    INDEX idx_user_video_progress_completed (completed),
    INDEX idx_user_video_progress_activity (last_watched_at DESC)
);

-- ==========================================
-- SQUAD SYSTEM
-- ==========================================

-- Squad definitions
CREATE TABLE squads (
    squad_id BIGSERIAL PRIMARY KEY,
    
    -- Squad details
    name VARCHAR(255) UNIQUE NOT NULL,
    tag VARCHAR(10) UNIQUE NOT NULL, -- Short tag like [ELITE]
    description TEXT,
    motto VARCHAR(500),
    
    -- Leadership
    leader_user_id BIGINT REFERENCES users(user_id),
    co_leaders JSONB DEFAULT '[]'::jsonb, -- Array of user_ids
    
    -- Squad stats
    member_count INTEGER DEFAULT 0,
    total_xp BIGINT DEFAULT 0,
    average_member_xp INTEGER DEFAULT 0,
    squad_level INTEGER DEFAULT 1,
    
    -- Requirements
    min_xp_requirement INTEGER DEFAULT 0,
    min_tier_requirement VARCHAR(50),
    max_members INTEGER DEFAULT 50,
    
    -- Squad features
    is_public BOOLEAN DEFAULT TRUE,
    is_recruiting BOOLEAN DEFAULT TRUE,
    recruitment_message TEXT,
    
    -- Achievements & rewards
    achievements JSONB DEFAULT '[]'::jsonb,
    squad_perks JSONB DEFAULT '[]'::jsonb, -- Special benefits for members
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    disbanded_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_squads_leader (leader_user_id),
    INDEX idx_squads_total_xp (total_xp DESC),
    INDEX idx_squads_level (squad_level DESC),
    INDEX idx_squads_recruiting (is_recruiting) WHERE is_recruiting = TRUE
);

-- Squad members
CREATE TABLE squad_members (
    member_id BIGSERIAL PRIMARY KEY,
    squad_id BIGINT NOT NULL REFERENCES squads(squad_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Member details
    role VARCHAR(50) DEFAULT 'member', -- leader, co_leader, officer, member
    rank_in_squad INTEGER, -- Internal squad ranking
    
    -- Contribution tracking
    xp_contributed BIGINT DEFAULT 0,
    missions_completed INTEGER DEFAULT 0,
    squad_activities_joined INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, inactive, suspended
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP WITH TIME ZONE,
    
    -- Permissions
    can_invite BOOLEAN DEFAULT FALSE,
    can_kick BOOLEAN DEFAULT FALSE,
    can_edit_squad BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(squad_id, user_id),
    INDEX idx_squad_members_user (user_id),
    INDEX idx_squad_members_squad (squad_id),
    INDEX idx_squad_members_xp (xp_contributed DESC)
);

-- Squad missions (collaborative missions)
CREATE TABLE squad_missions (
    squad_mission_id BIGSERIAL PRIMARY KEY,
    
    -- Mission details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    mission_type VARCHAR(50) NOT NULL, -- collective_xp, trading_volume, win_rate, recruitment
    
    -- Requirements
    requirements JSONB NOT NULL, -- {collective_xp: 50000, time_limit_hours: 168}
    
    -- Progress tracking
    current_progress JSONB DEFAULT '{}'::jsonb,
    progress_percent INTEGER DEFAULT 0,
    
    -- Participants
    participating_squads JSONB DEFAULT '[]'::jsonb, -- Squad IDs participating
    
    -- Rewards
    rewards JSONB NOT NULL, -- {xp_per_member: 1000, squad_xp: 5000, badges: [...]}
    
    -- Timing
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    status VARCHAR(50) DEFAULT 'upcoming', -- upcoming, active, completed, failed
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_squad_missions_status (status),
    INDEX idx_squad_missions_start (start_time),
    INDEX idx_squad_missions_type (mission_type)
);

-- Squad mission participation
CREATE TABLE squad_mission_participation (
    participation_id BIGSERIAL PRIMARY KEY,
    squad_mission_id BIGINT NOT NULL REFERENCES squad_missions(squad_mission_id),
    squad_id BIGINT NOT NULL REFERENCES squads(squad_id),
    
    -- Progress
    contribution JSONB DEFAULT '{}'::jsonb, -- Squad-specific contribution
    rank INTEGER, -- Final ranking in the mission
    
    -- Rewards
    rewards_earned JSONB DEFAULT '{}'::jsonb,
    rewards_claimed BOOLEAN DEFAULT FALSE,
    
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(squad_mission_id, squad_id),
    INDEX idx_squad_participation_squad (squad_id),
    INDEX idx_squad_participation_mission (squad_mission_id)
);

-- ==========================================
-- MENTORSHIP SYSTEM
-- ==========================================

-- Mentorship relationships
CREATE TABLE mentorships (
    mentorship_id BIGSERIAL PRIMARY KEY,
    mentor_user_id BIGINT NOT NULL REFERENCES users(user_id),
    mentee_user_id BIGINT NOT NULL REFERENCES users(user_id),
    
    -- Relationship details
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, active, completed, cancelled
    mentorship_type VARCHAR(50), -- general, trading_basics, risk_management, psychology
    
    -- Progress tracking
    sessions_completed INTEGER DEFAULT 0,
    total_interaction_minutes INTEGER DEFAULT 0,
    goals_achieved JSONB DEFAULT '[]'::jsonb,
    
    -- Feedback
    mentee_rating INTEGER CHECK (mentee_rating >= 1 AND mentee_rating <= 5),
    mentor_rating INTEGER CHECK (mentor_rating >= 1 AND mentor_rating <= 5),
    mentee_feedback TEXT,
    mentor_feedback TEXT,
    
    -- Rewards
    mentor_xp_earned INTEGER DEFAULT 0,
    mentee_xp_earned INTEGER DEFAULT 0,
    
    -- Timestamps
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    last_interaction_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(mentor_user_id, mentee_user_id),
    INDEX idx_mentorships_mentor (mentor_user_id),
    INDEX idx_mentorships_mentee (mentee_user_id),
    INDEX idx_mentorships_status (status),
    INDEX idx_mentorships_active (status) WHERE status = 'active'
);

-- Mentor profiles
CREATE TABLE mentor_profiles (
    mentor_profile_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL REFERENCES users(user_id),
    
    -- Qualifications
    specializations JSONB DEFAULT '[]'::jsonb, -- ["risk_management", "scalping", "psychology"]
    min_tier_to_mentor VARCHAR(50) DEFAULT 'NIBBLER',
    
    -- Stats
    total_mentees INTEGER DEFAULT 0,
    active_mentees INTEGER DEFAULT 0,
    completed_mentorships INTEGER DEFAULT 0,
    average_rating DECIMAL(3,2),
    total_ratings INTEGER DEFAULT 0,
    
    -- Availability
    is_accepting_mentees BOOLEAN DEFAULT TRUE,
    max_concurrent_mentees INTEGER DEFAULT 3,
    preferred_communication JSONB DEFAULT '[]'::jsonb, -- ["chat", "voice", "video"]
    availability_schedule JSONB DEFAULT '{}'::jsonb, -- Weekly schedule
    
    -- Profile
    bio TEXT,
    teaching_style TEXT,
    success_stories JSONB DEFAULT '[]'::jsonb,
    
    -- Achievements
    mentor_level INTEGER DEFAULT 1,
    mentor_xp INTEGER DEFAULT 0,
    badges_earned JSONB DEFAULT '[]'::jsonb,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_mentor_profiles_rating (average_rating DESC),
    INDEX idx_mentor_profiles_accepting (is_accepting_mentees) WHERE is_accepting_mentees = TRUE
);

-- ==========================================
-- STUDY GROUPS
-- ==========================================

-- Study groups
CREATE TABLE study_groups (
    group_id BIGSERIAL PRIMARY KEY,
    
    -- Group details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    topic VARCHAR(100) NOT NULL, -- specific trading topic or strategy
    difficulty_level VARCHAR(50),
    
    -- Organization
    creator_user_id BIGINT NOT NULL REFERENCES users(user_id),
    moderators JSONB DEFAULT '[]'::jsonb, -- Array of user_ids
    
    -- Schedule
    schedule_type VARCHAR(50) DEFAULT 'recurring', -- one_time, recurring
    schedule_data JSONB NOT NULL, -- {day: "Monday", time: "18:00", timezone: "UTC", duration_minutes: 60}
    next_session_at TIMESTAMP WITH TIME ZONE,
    
    -- Participation
    max_participants INTEGER DEFAULT 20,
    current_participants INTEGER DEFAULT 0,
    min_tier_requirement VARCHAR(50),
    
    -- Progress
    sessions_held INTEGER DEFAULT 0,
    total_study_hours INTEGER DEFAULT 0,
    completion_rate DECIMAL(5,2), -- Percentage of scheduled sessions completed
    
    -- Resources
    study_materials JSONB DEFAULT '[]'::jsonb, -- Links to videos, documents, etc.
    
    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, paused, completed, cancelled
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_study_groups_creator (creator_user_id),
    INDEX idx_study_groups_topic (topic),
    INDEX idx_study_groups_next_session (next_session_at),
    INDEX idx_study_groups_status (status)
);

-- Study group participants
CREATE TABLE study_group_participants (
    participant_id BIGSERIAL PRIMARY KEY,
    group_id BIGINT NOT NULL REFERENCES study_groups(group_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Participation
    role VARCHAR(50) DEFAULT 'member', -- creator, moderator, member
    sessions_attended INTEGER DEFAULT 0,
    attendance_rate DECIMAL(5,2),
    
    -- Engagement
    contributions_count INTEGER DEFAULT 0, -- Questions asked, answers provided
    helpful_votes_received INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, inactive, removed
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_attended_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(group_id, user_id),
    INDEX idx_study_participants_user (user_id),
    INDEX idx_study_participants_group (group_id)
);

-- ==========================================
-- ACHIEVEMENT PROGRESS & SHOWCASE
-- ==========================================

-- Achievement categories specific to education
CREATE TABLE education_achievement_categories (
    category_id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    icon_url VARCHAR(500),
    display_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Extended achievement progress with showcase
CREATE TABLE user_achievement_progress (
    progress_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    achievement_id BIGINT NOT NULL REFERENCES achievements(achievement_id),
    
    -- Progress details
    current_value DECIMAL(15,2) DEFAULT 0,
    target_value DECIMAL(15,2) NOT NULL,
    progress_percent INTEGER DEFAULT 0,
    
    -- Milestones
    milestones_completed JSONB DEFAULT '[]'::jsonb, -- [25, 50, 75] percentages
    last_milestone_at TIMESTAMP WITH TIME ZONE,
    
    -- Showcase
    is_showcased BOOLEAN DEFAULT FALSE,
    showcase_slot INTEGER, -- 1-5 for profile showcase
    showcase_priority INTEGER DEFAULT 0,
    
    -- Tracking
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, achievement_id),
    INDEX idx_achievement_progress_user (user_id),
    INDEX idx_achievement_progress_percent (progress_percent DESC),
    INDEX idx_achievement_progress_showcase (user_id, is_showcased) WHERE is_showcased = TRUE
);

-- ==========================================
-- EDUCATION METRICS & ANALYTICS
-- ==========================================

-- Daily education metrics per user
CREATE TABLE user_education_metrics (
    metric_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    
    -- Video metrics
    videos_watched INTEGER DEFAULT 0,
    video_minutes_watched INTEGER DEFAULT 0,
    videos_completed INTEGER DEFAULT 0,
    
    -- Mission metrics
    missions_started INTEGER DEFAULT 0,
    missions_completed INTEGER DEFAULT 0,
    objectives_completed INTEGER DEFAULT 0,
    
    -- Quiz metrics
    quizzes_attempted INTEGER DEFAULT 0,
    quizzes_passed INTEGER DEFAULT 0,
    average_quiz_score DECIMAL(5,2),
    
    -- Engagement metrics
    study_group_minutes INTEGER DEFAULT 0,
    mentorship_minutes INTEGER DEFAULT 0,
    forum_posts INTEGER DEFAULT 0,
    helpful_votes_given INTEGER DEFAULT 0,
    helpful_votes_received INTEGER DEFAULT 0,
    
    -- XP earned from education
    education_xp_earned INTEGER DEFAULT 0,
    
    -- Streaks
    learning_streak_days INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, metric_date),
    INDEX idx_education_metrics_user_date (user_id, metric_date DESC),
    INDEX idx_education_metrics_date (metric_date DESC)
);

-- Global education analytics
CREATE TABLE education_analytics (
    analytics_id BIGSERIAL PRIMARY KEY,
    analytics_date DATE NOT NULL,
    
    -- User engagement
    daily_active_learners INTEGER DEFAULT 0,
    weekly_active_learners INTEGER DEFAULT 0,
    monthly_active_learners INTEGER DEFAULT 0,
    
    -- Content metrics
    total_video_views INTEGER DEFAULT 0,
    total_video_minutes INTEGER DEFAULT 0,
    average_video_completion_rate DECIMAL(5,2),
    most_watched_videos JSONB DEFAULT '[]'::jsonb,
    
    -- Mission metrics
    missions_started INTEGER DEFAULT 0,
    missions_completed INTEGER DEFAULT 0,
    average_mission_completion_rate DECIMAL(5,2),
    
    -- Squad metrics
    active_squads INTEGER DEFAULT 0,
    new_squads_created INTEGER DEFAULT 0,
    squad_missions_completed INTEGER DEFAULT 0,
    
    -- Mentorship metrics
    active_mentorships INTEGER DEFAULT 0,
    new_mentorships_started INTEGER DEFAULT 0,
    mentorships_completed INTEGER DEFAULT 0,
    average_mentor_rating DECIMAL(3,2),
    
    -- Study group metrics
    active_study_groups INTEGER DEFAULT 0,
    study_sessions_held INTEGER DEFAULT 0,
    average_attendance_rate DECIMAL(5,2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(analytics_date),
    INDEX idx_education_analytics_date (analytics_date DESC)
);

-- User learning paths (recommended sequences)
CREATE TABLE user_learning_paths (
    path_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Path details
    path_name VARCHAR(255) NOT NULL,
    path_type VARCHAR(50) NOT NULL, -- custom, recommended, mandatory
    
    -- Content sequence
    content_sequence JSONB NOT NULL, -- [{type: "video", id: 123}, {type: "mission", id: 456}]
    
    -- Progress
    current_position INTEGER DEFAULT 0,
    completed_items JSONB DEFAULT '[]'::jsonb,
    completion_percent INTEGER DEFAULT 0,
    
    -- Timestamps
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    last_activity_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_learning_paths_user (user_id),
    INDEX idx_learning_paths_type (path_type),
    INDEX idx_learning_paths_completion (completion_percent)
);

-- ==========================================
-- PERFORMANCE INDEXES
-- ==========================================

-- Composite indexes for common queries
CREATE INDEX idx_user_education_overview ON user_mission_progress(user_id, status, completed_at DESC);
CREATE INDEX idx_squad_leaderboard ON squads(total_xp DESC, squad_level DESC) WHERE disbanded_at IS NULL;
CREATE INDEX idx_mentor_search ON mentor_profiles(is_accepting_mentees, average_rating DESC) WHERE is_accepting_mentees = TRUE;
CREATE INDEX idx_video_recommendations ON education_videos(category, difficulty_level, view_count DESC) WHERE is_active = TRUE;
CREATE INDEX idx_active_study_sessions ON study_groups(next_session_at, status) WHERE status = 'active';
CREATE INDEX idx_user_achievements_showcase ON user_achievement_progress(user_id, showcase_slot) WHERE is_showcased = TRUE;

-- Full text search indexes
CREATE INDEX idx_mission_search ON education_missions USING gin(to_tsvector('english', name || ' ' || description));
CREATE INDEX idx_video_search ON education_videos USING gin(to_tsvector('english', title || ' ' || description));
CREATE INDEX idx_squad_search ON squads USING gin(to_tsvector('english', name || ' ' || description));

-- ==========================================
-- TRIGGERS FOR AUTOMATED UPDATES
-- ==========================================

-- Update squad statistics when members change
CREATE OR REPLACE FUNCTION update_squad_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE squads s
        SET 
            member_count = (SELECT COUNT(*) FROM squad_members WHERE squad_id = NEW.squad_id AND status = 'active'),
            total_xp = (SELECT SUM(xp_contributed) FROM squad_members WHERE squad_id = NEW.squad_id AND status = 'active'),
            average_member_xp = (SELECT AVG(xp_contributed)::INTEGER FROM squad_members WHERE squad_id = NEW.squad_id AND status = 'active'),
            updated_at = CURRENT_TIMESTAMP
        WHERE squad_id = NEW.squad_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE squads s
        SET 
            member_count = (SELECT COUNT(*) FROM squad_members WHERE squad_id = OLD.squad_id AND status = 'active'),
            total_xp = (SELECT SUM(xp_contributed) FROM squad_members WHERE squad_id = OLD.squad_id AND status = 'active'),
            average_member_xp = (SELECT AVG(xp_contributed)::INTEGER FROM squad_members WHERE squad_id = OLD.squad_id AND status = 'active'),
            updated_at = CURRENT_TIMESTAMP
        WHERE squad_id = OLD.squad_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_squad_stats_trigger
AFTER INSERT OR UPDATE OR DELETE ON squad_members
FOR EACH ROW EXECUTE FUNCTION update_squad_stats();

-- Update video view count
CREATE OR REPLACE FUNCTION increment_video_views()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE education_videos
    SET view_count = view_count + 1
    WHERE video_id = NEW.video_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER increment_video_views_trigger
AFTER INSERT ON user_video_progress
FOR EACH ROW EXECUTE FUNCTION increment_video_views();

-- Calculate achievement progress
CREATE OR REPLACE FUNCTION update_achievement_progress()
RETURNS TRIGGER AS $$
BEGIN
    NEW.progress_percent = LEAST(100, FLOOR((NEW.current_value / NEW.target_value) * 100));
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_achievement_progress_trigger
BEFORE UPDATE ON user_achievement_progress
FOR EACH ROW EXECUTE FUNCTION update_achievement_progress();

-- Update user mission progress percent
CREATE OR REPLACE FUNCTION calculate_mission_progress()
RETURNS TRIGGER AS $$
DECLARE
    total_objectives INTEGER;
    completed_objectives INTEGER;
BEGIN
    -- Get total objectives for the mission
    SELECT jsonb_array_length(objectives)
    INTO total_objectives
    FROM education_missions
    WHERE mission_id = NEW.mission_id;
    
    -- Get completed objectives count
    completed_objectives := jsonb_array_length(NEW.objectives_completed);
    
    -- Calculate progress percent
    IF total_objectives > 0 THEN
        NEW.progress_percent = FLOOR((completed_objectives::DECIMAL / total_objectives) * 100);
    END IF;
    
    -- Update status if completed
    IF NEW.progress_percent = 100 AND NEW.status != 'completed' THEN
        NEW.status = 'completed';
        NEW.completed_at = CURRENT_TIMESTAMP;
    END IF;
    
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_mission_progress_trigger
BEFORE UPDATE ON user_mission_progress
FOR EACH ROW EXECUTE FUNCTION calculate_mission_progress();

-- ==========================================
-- INITIAL DATA SEEDS
-- ==========================================

-- Insert education achievement categories
INSERT INTO education_achievement_categories (code, name, description, display_order) VALUES
('learning_basics', 'Learning Basics', 'Foundational education achievements', 1),
('video_mastery', 'Video Mastery', 'Video watching and completion achievements', 2),
('mission_expert', 'Mission Expert', 'Mission completion achievements', 3),
('quiz_champion', 'Quiz Champion', 'Quiz performance achievements', 4),
('squad_leader', 'Squad Leader', 'Squad participation and leadership', 5),
('mentor_master', 'Mentor Master', 'Mentorship achievements', 6),
('study_scholar', 'Study Scholar', 'Study group achievements', 7),
('streak_warrior', 'Streak Warrior', 'Learning streak achievements', 8);

-- ==========================================
-- PERMISSIONS (Run as superuser)
-- ==========================================

-- Grant permissions to application user
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bitten_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO bitten_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO bitten_app;

-- ==========================================
-- MIGRATION COMPLETE
-- ==========================================

-- Migration version tracking
CREATE TABLE IF NOT EXISTS migration_history (
    migration_id BIGSERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO migration_history (filename) VALUES ('education_tables.sql');