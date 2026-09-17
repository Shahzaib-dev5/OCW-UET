ALTER TABLE `research_papers`
    ADD COLUMN IF NOT EXISTS `publication_date` DATE NULL AFTER `conference_name`;

CREATE INDEX IF NOT EXISTS `idx_research_publication_date`
    ON `research_papers` (`publication_date`);
