-- 1. Which actors share the MOST entities with another actor?
-- (strongest "same person?" candidates)
MATCH (a1:Actor)-[:USES]->(e)<-[:USES]-(a2:Actor)
WHERE a1.actor_id < a2.actor_id
RETURN a1.actor_id, a1.username, a2.actor_id, a2.username, count(e) AS shared_entities
ORDER BY shared_entities DESC
LIMIT 10;

-- 2. Show one specific actor's full evidence web (replace 2 with any real actor_id)
MATCH (a:Actor {actor_id: 2})-[:USES]->(e)
RETURN a, e;

-- 3. Which PGP keys are shared by more than one actor? (strong signal)
MATCH (a:Actor)-[:USES]->(p:PGP)
WITH p, count(a) AS actor_count
WHERE actor_count > 1
MATCH (a:Actor)-[:USES]->(p)
RETURN p.value, collect(a.actor_id) AS actor_ids, actor_count
ORDER BY actor_count DESC;

-- 4. Which wallets are shared by more than one actor?
MATCH (a:Actor)-[:USES]->(w:Wallet)
WITH w, count(a) AS actor_count
WHERE actor_count > 1
MATCH (a:Actor)-[:USES]->(w)
RETURN w.value, collect(a.actor_id) AS actor_ids, actor_count
ORDER BY actor_count DESC;

-- 5. Most active forums (by post count)
MATCH (p:Post)-[:POSTED_ON]->(pl:Platform)
RETURN pl.forum_name, count(p) AS post_count
ORDER BY post_count DESC
LIMIT 10;

-- 6. Full reply chain / conversation thread starting from a specific post
MATCH path = (p:Post {post_id: 2591})-[:REPLIED_TO*1..5]->(root:Post)
RETURN path;

-- 7. Actors with the most posts (most active users)
MATCH (a:Actor)
RETURN a.actor_id, a.username, a.post_count
ORDER BY a.post_count DESC
LIMIT 10;

-- 8. The full picture: one actor, their posts, their entities, all together
MATCH (a:Actor {actor_id: 2})
OPTIONAL MATCH (a)-[:USES]->(e)
OPTIONAL MATCH (a)-[:POSTED]->(p:Post)
RETURN a, e, p
LIMIT 50;

-- 9. Count how many actors use each entity type (overview)
MATCH (a:Actor)-[:USES]->(e)
RETURN labels(e)[0] AS entity_type, count(DISTINCT e) AS unique_entities, count(a) AS total_links
ORDER BY unique_entities DESC;

-- 10. Find actors connected to the makikaki anomaly (should show the data_quality_flag)
MATCH (a:Actor {actor_id: 110})
RETURN a;
