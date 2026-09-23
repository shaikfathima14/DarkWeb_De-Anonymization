-- 1. Count of each relationship type
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(r) AS count
ORDER BY count DESC;

-- 2. See a sample of each relationship type visually (10 of each)
MATCH (a)-[r:USES]->(b) RETURN a, r, b LIMIT 10;

MATCH (a)-[r:POSTED]->(b) RETURN a, r, b LIMIT 10;

MATCH (a)-[r:POSTED_ON]->(b) RETURN a, r, b LIMIT 10;

MATCH (a)-[r:REPLIED_TO]->(b) RETURN a, r, b LIMIT 10;

-- 3. See ALL relationship types together in one small visual sample
MATCH (a)-[r]->(b)
RETURN a, r, b
LIMIT 100;

-- 4. For one specific actor, show every relationship they're part of (any type, any direction)
MATCH (a:Actor {actor_id: 2})-[r]-(other)
RETURN a, r, other;
