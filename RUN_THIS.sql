use photoshare;
ALTER TABLE Pictures
ADD COLUMN likes int4 DEFAULT 0;

ALTER TABLE photoshare.Users
ADD COLUMN profile_img longblob;

