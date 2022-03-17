use photoshare;
SELECT tag_id, text
FROM (
	SELECT T.tag_id, text,picture_id
	FROM has_tag HT
	JOIN Tags T on HT.tag_id = T.tag_id
    )
	AS TagInfo
GROUP BY tag_id, text
ORDER BY COUNT(picture_id) DESC
