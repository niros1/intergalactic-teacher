-- Clean all story-related data while preserving users and children
-- Run this script to reset story data in the database

-- Start transaction for safety
BEGIN;

-- Delete in order of dependencies (most dependent first)

-- 1. Delete all story sessions (reading history)
DELETE FROM story_sessions;

-- 2. Delete all story branches
DELETE FROM story_branches;

-- 3. Delete all choices
DELETE FROM choices;

-- 4. Delete all stories
DELETE FROM stories;

-- Reset sequences if needed (PostgreSQL)
-- This ensures new stories start from ID 1
ALTER SEQUENCE IF EXISTS stories_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS choices_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS story_branches_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS story_sessions_id_seq RESTART WITH 1;

-- Verify what remains (should show users and children tables intact)
SELECT 'Users count:' as info, COUNT(*) as count FROM users
UNION ALL
SELECT 'Children count:', COUNT(*) FROM children
UNION ALL
SELECT 'Stories count (should be 0):', COUNT(*) FROM stories
UNION ALL
SELECT 'Sessions count (should be 0):', COUNT(*) FROM story_sessions;

-- Commit the transaction
COMMIT;

-- Show confirmation
SELECT 'Story data cleanup complete!' as status;