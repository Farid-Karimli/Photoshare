
-- friends of friends 
use photoshare;
SELECT user2
FROM (
	SELECT F1.user1,F1.user2
	FROM Friends_with F
	INNER JOIN Friends_with F1 WHERE F.user1=3 and F.user2 = F1.user1 and not F1.user2 = 3)
    as FF
WHERE not user2  IN (SELECT user2 FROM Friends_with WHERE user1 = 3)
GROUP BY user2
ORDER BY COUNT(user2) DESC

-- most popular albums
SELECT album_id, album_name, date_created, owner,cover_img
FROM 
    (SELECT A.*, P.likes FROM Albums A CROSS JOIN Pictures P ON A.album_id = P.album_id)
    AS A1
GROUP BY album_id, album_name, date_created, owner,cover_img
ORDER BY SUM(likes) DESC
LIMIT 5;

-- most popular tags
SELECT tag_id, text
FROM (
	SELECT T.tag_id, text,picture_id
	FROM has_tag HT
	JOIN Tags T on HT.tag_id = T.tag_id
    )
	AS TagInfo
GROUP BY tag_id, text
ORDER BY COUNT(picture_id) DESC

-- query to get the top 5 tags of the given user
SELECT * FROM
	(SELECT T.tag_id 
	 FROM has_tag H, Pictures P, tags t 
	 WHERE P.picture_id =H.Picture_id 
	 AND T.tag_id = H.tag_id
	 AND P.user_id = 3
	 GROUP BY H.tag_id, P.user_id
	 ORDER BY count(*) DESC LIMIT 5 ) AS top_tags;

-- you may also like query
SELECT X.picture_id FROM(
SELECT P.picture_id, Count(H.tag_id) AS CNUMTAGS 
FROM HAS_Tag H, ((SELECT t1.picture_id, COUNT(*) AS CMATCH FROM (
  (SELECT DISTINCT P.picture_id FROM has_tag H, Pictures P WHERE P.picture_id = H.picture_id AND H.tag_id = 1 AND P.user_id != 3)
  UNION ALL 
  (SELECT DISTINCT P.picture_id FROM has_tag H, Pictures P WHERE P.picture_id = H.picture_id AND H.tag_id = 3 AND P.user_id != 3)
  UNION ALL
  (SELECT DISTINCT P.picture_id FROM has_tag H, Pictures P WHERE P.picture_id = H.picture_id AND H.tag_id = 2 AND P.user_id != 3)
  UNION ALL 
  (SELECT DISTINCT P.picture_id FROM has_tag H, Pictures P WHERE P.picture_id = H.picture_id AND H.tag_id =7 AND P.user_id != 3)
  UNION ALL
  (SELECT DISTINCT P.picture_id FROM has_tag H, Pictures P WHERE P.picture_id = H.picture_id AND H.tag_id = 10 AND P.user_id != 3)
) AS t1 GROUP BY picture_id HAVING count(*) >= 1 ORDER BY CMATCH DESC)) P
WHERE P.picture_id = H.picture_id GROUP BY P.picture_id ORDER BY P.CMATCH DESC, CNUMTAGS ASC LIMIT 5) X;

-- you may also like query 2
SELECT HT2.picture_id, COUNT(HT2.tag_id) FROM
(SELECT T.tag_id, text
FROM Tags T, Has_tag HT, Pictures P
WHERE HT.tag_id = T.tag_id AND HT.picture_id = P.picture_id AND P.user_id = 4
GROUP BY T.tag_id
ORDER BY Count(T.tag_id) DESC
LIMIT 5)
AS popular_tags
JOIN Has_tag HT2, Pictures P2
WHERE popular_tags.tag_id = HT2.tag_id AND P2.picture_id = HT2.picture_id
GROUP BY HT2.picture_id
ORDER BY Count(HT2.tag_id) DESC

	



