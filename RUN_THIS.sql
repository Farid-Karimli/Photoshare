use photoshare;
ALTER TABLE Pictures
ADD COLUMN likes int4 DEFAULT 0;

ALTER TABLE photoshare.Users
ADD COLUMN profile_img longblob;

CREATE TABLE likes(
	user_id int4,
    photo_id int4,
    
    PRIMARY KEY(user_id, photo_id),
    FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY(photo_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE

);
use photoshare;
ALTER TABLE ALBUMS
ALTER COLUMN date_created SET DEFAULT (DATE_FORMAT(NOW(), '%y-%m-%d'));


