use photoshare;
ALTER TABLE Pictures
ADD COLUMN likes int4 DEFAULT 0;

