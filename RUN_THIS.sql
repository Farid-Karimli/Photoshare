
use photoshare;
SELECT * FROM
(SELECT H.tag_id,H.picture_id,T.text FROM has_tag H
	INNER JOIN Tags T
	ON T.tag_id = H.tag_id) as Tags_Text
right JOIN temp ON Tags_Text.text = temp.search



