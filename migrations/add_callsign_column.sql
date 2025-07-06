-- Add callsign column to user_profiles table
-- This allows users to have a unique callsign identity in the BITTEN network

-- Add the column (nullable initially to handle existing records)
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS callsign VARCHAR(50);

-- Create unique index on callsign (excluding NULL values)
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_profiles_callsign 
ON user_profiles (callsign) 
WHERE callsign IS NOT NULL;

-- Comment on the column
COMMENT ON COLUMN user_profiles.callsign IS 'User unique callsign/nickname in the BITTEN network';

-- Update existing users with default callsigns based on their user_id
-- This ensures existing users get a placeholder callsign
UPDATE user_profiles 
SET callsign = 'Soldier' || user_id::text 
WHERE callsign IS NULL;