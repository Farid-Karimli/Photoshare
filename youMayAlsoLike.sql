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
