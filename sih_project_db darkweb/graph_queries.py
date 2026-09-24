"""
SIH26151 - Graph Query Functions (Person 5's tool layer for Person 2's agent)

These functions are meant to be called by Person 2's agent orchestrator as
"tools" - each one returns evidence for ONE specific type, so the agent can
call them one at a time and stream results to the frontend incrementally
(instead of dumping the whole graph at once).

Every function returns the SAME shape, so Person 1's frontend can render
any of them the same way:

{
  "nodes": [ {"id": "...", "label": "...", "type": "Actor|PGP|Wallet|...", "properties": {...}} ],
  "edges": [ {"source": "...", "target": "...", "type": "USES|POSTED|..."} ]
}

Usage (by Person 2, in his own code):
    from graph_queries import GraphQueries
    gq = GraphQueries(uri, user, password)
    result = gq.get_pgp_relationships(actor_id=2)
    gq.close()
"""

from neo4j import GraphDatabase


class GraphQueries:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def _node_to_dict(self, node, node_type):
        """Convert a Neo4j node into the standard dict shape."""
        props = dict(node)
        node_id = f"{node_type}_{props.get('actor_id') or props.get('post_id') or props.get('forum_id') or props.get('value')}"
        return {"id": node_id, "label": node_type, "type": node_type, "properties": props}

    def _run_entity_query(self, actor_id, entity_label):
        """Shared logic for get_pgp_relationships, get_wallet_relationships, etc."""
        query = f"""
        MATCH (a:Actor {{actor_id: $actor_id}})-[:USES]->(e:{entity_label})
        OPTIONAL MATCH (other:Actor)-[:USES]->(e)
        WHERE other.actor_id <> a.actor_id
        RETURN a, e, collect(DISTINCT other) AS other_actors
        """
        nodes = {}
        edges = []
        with self.driver.session() as session:
            result = session.run(query, actor_id=actor_id)
            for record in result:
                a_node = self._node_to_dict(record["a"], "Actor")
                e_node = self._node_to_dict(record["e"], entity_label)
                nodes[a_node["id"]] = a_node
                nodes[e_node["id"]] = e_node
                edges.append({"source": a_node["id"], "target": e_node["id"], "type": "USES"})

                for other in record["other_actors"]:
                    other_node = self._node_to_dict(other, "Actor")
                    nodes[other_node["id"]] = other_node
                    edges.append({"source": other_node["id"], "target": e_node["id"], "type": "USES"})

        return {"nodes": list(nodes.values()), "edges": edges}

    # ---------- Tool functions Person 2's agent calls ----------

    def get_pgp_relationships(self, actor_id):
        """Returns this actor's PGP key(s) and any OTHER actor sharing the same key."""
        return self._run_entity_query(actor_id, "PGP")

    def get_wallet_relationships(self, actor_id):
        """Returns this actor's wallet(s) and any OTHER actor sharing the same wallet."""
        return self._run_entity_query(actor_id, "Wallet")

    def get_email_relationships(self, actor_id):
        """Returns this actor's email(s) and any OTHER actor sharing the same email."""
        return self._run_entity_query(actor_id, "Email")

    def get_infrastructure_relationships(self, actor_id):
        """Returns this actor's onion/IP-TLS infrastructure and any OTHER actor sharing it."""
        return self._run_entity_query(actor_id, "Infrastructure")

    def get_all_relationships(self, actor_id):
        """Returns EVERYTHING for one actor: all entities + posts + platforms in one call.
        Use this only if the agent needs the full picture at once, not incrementally."""
        query = """
        MATCH (a:Actor {actor_id: $actor_id})
        OPTIONAL MATCH (a)-[:USES]->(e)
        OPTIONAL MATCH (a)-[:POSTED]->(p:Post)-[:POSTED_ON]->(pl:Platform)
        RETURN a, collect(DISTINCT e) AS entities, collect(DISTINCT p) AS posts, collect(DISTINCT pl) AS platforms
        """
        nodes = {}
        edges = []
        with self.driver.session() as session:
            result = session.run(query, actor_id=actor_id)
            for record in result:
                a_node = self._node_to_dict(record["a"], "Actor")
                nodes[a_node["id"]] = a_node

                for e in record["entities"]:
                    if e is None:
                        continue
                    e_type = list(e.labels)[0]
                    e_node = self._node_to_dict(e, e_type)
                    nodes[e_node["id"]] = e_node
                    edges.append({"source": a_node["id"], "target": e_node["id"], "type": "USES"})

                for p in record["posts"]:
                    if p is None:
                        continue
                    p_node = self._node_to_dict(p, "Post")
                    nodes[p_node["id"]] = p_node
                    edges.append({"source": a_node["id"], "target": p_node["id"], "type": "POSTED"})

                for pl in record["platforms"]:
                    if pl is None:
                        continue
                    pl_node = self._node_to_dict(pl, "Platform")
                    nodes[pl_node["id"]] = pl_node

        return {"nodes": list(nodes.values()), "edges": edges}

    def get_shared_entities_between(self, actor_id_a, actor_id_b):
        """Returns ONLY the entities shared between two specific actors (used for
        direct 'are these the same person?' comparisons)."""
        query = """
        MATCH (a1:Actor {actor_id: $id_a})-[:USES]->(e)<-[:USES]-(a2:Actor {actor_id: $id_b})
        RETURN a1, a2, collect(DISTINCT e) AS shared
        """
        nodes = {}
        edges = []
        with self.driver.session() as session:
            result = session.run(query, id_a=actor_id_a, id_b=actor_id_b)
            for record in result:
                a1_node = self._node_to_dict(record["a1"], "Actor")
                a2_node = self._node_to_dict(record["a2"], "Actor")
                nodes[a1_node["id"]] = a1_node
                nodes[a2_node["id"]] = a2_node

                for e in record["shared"]:
                    e_type = list(e.labels)[0]
                    e_node = self._node_to_dict(e, e_type)
                    nodes[e_node["id"]] = e_node
                    edges.append({"source": a1_node["id"], "target": e_node["id"], "type": "USES"})
                    edges.append({"source": a2_node["id"], "target": e_node["id"], "type": "USES"})

        return {"nodes": list(nodes.values()), "edges": edges}

    def get_reply_chain(self, post_id, depth=5):
        """Returns the reply chain (thread) leading from a given post."""
        query = """
        MATCH path = (p:Post {post_id: $post_id})-[:REPLIED_TO*1..%d]->(root:Post)
        RETURN path
        """ % depth
        nodes = {}
        edges = []
        with self.driver.session() as session:
            result = session.run(query, post_id=post_id)
            for record in result:
                path = record["path"]
                for node in path.nodes:
                    n_dict = self._node_to_dict(node, "Post")
                    nodes[n_dict["id"]] = n_dict
                for rel in path.relationships:
                    edges.append({
                        "source": f"Post_{rel.start_node['post_id']}",
                        "target": f"Post_{rel.end_node['post_id']}",
                        "type": "REPLIED_TO",
                    })

        return {"nodes": list(nodes.values()), "edges": edges}


# ---------- Example usage / quick test ----------
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    gq = GraphQueries(
        os.getenv("NEO4J_URI"),
        os.getenv("NEO4J_USER"),
        os.getenv("NEO4J_PASSWORD"),
    )

    # quick test - swap in a real actor_id from your data
    result = gq.get_pgp_relationships(actor_id=2)
    print(f"Nodes: {len(result['nodes'])}, Edges: {len(result['edges'])}")

    gq.close()
