"""Build knowledge graph for movies, actors, and directors."""
import networkx as nx
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    """Build and query knowledge graphs."""

    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.node_types = {}  # Track node types

    def add_movie(self, movie_id: int, title: str, **attributes):
        """Add a movie node to the graph."""
        self.graph.add_node(f"movie_{movie_id}", type="movie", title=title, **attributes)
        self.node_types[f"movie_{movie_id}"] = "movie"

    def add_actor(self, actor_id: int, name: str, **attributes):
        """Add an actor node to the graph."""
        self.graph.add_node(f"actor_{actor_id}", type="actor", name=name, **attributes)
        self.node_types[f"actor_{actor_id}"] = "actor"

    def add_director(self, director_id: int, name: str, **attributes):
        """Add a director node to the graph."""
        self.graph.add_node(f"director_{director_id}", type="director", name=name, **attributes)
        self.node_types[f"director_{director_id}"] = "director"

    def add_genre(self, genre_id: int, name: str):
        """Add a genre node to the graph."""
        self.graph.add_node(f"genre_{genre_id}", type="genre", name=name)
        self.node_types[f"genre_{genre_id}"] = "genre"

    def add_actor_to_movie(self, actor_id: int, movie_id: int, character: str = ""):
        """Add edge between actor and movie."""
        self.graph.add_edge(
            f"actor_{actor_id}",
            f"movie_{movie_id}",
            relation="acted_in",
            character=character,
        )

    def add_director_to_movie(self, director_id: int, movie_id: int):
        """Add edge between director and movie."""
        self.graph.add_edge(
            f"director_{director_id}",
            f"movie_{movie_id}",
            relation="directed",
        )

    def add_genre_to_movie(self, genre_id: int, movie_id: int):
        """Add edge between genre and movie."""
        self.graph.add_edge(
            f"movie_{movie_id}",
            f"genre_{genre_id}",
            relation="has_genre",
        )

    def get_actor_movies(self, actor_id: int) -> List[str]:
        """Get all movies an actor has appeared in."""
        actor_node = f"actor_{actor_id}"
        if actor_node not in self.graph:
            return []
        return list(self.graph.successors(actor_node))

    def get_director_movies(self, director_id: int) -> List[str]:
        """Get all movies a director has directed."""
        director_node = f"director_{director_id}"
        if director_node not in self.graph:
            return []
        return list(self.graph.successors(director_node))

    def get_movie_genres(self, movie_id: int) -> List[str]:
        """Get all genres for a movie."""
        movie_node = f"movie_{movie_id}"
        if movie_node not in self.graph:
            return []
        return list(self.graph.successors(movie_node))

    def get_movie_cast(self, movie_id: int) -> List[Tuple[str, Dict]]:
        """Get all actors in a movie with their characters."""
        movie_node = f"movie_{movie_id}"
        if movie_node not in self.graph:
            return []
        cast = []
        for pred in self.graph.predecessors(movie_node):
            if self.node_types.get(pred) == "actor":
                edge_data = self.graph.get_edge_data(pred, movie_node)
                for key, data in edge_data.items():
                    cast.append((pred, data))
        return cast

    def get_movie_directors(self, movie_id: int) -> List[str]:
        """Get all directors of a movie."""
        movie_node = f"movie_{movie_id}"
        if movie_node not in self.graph:
            return []
        directors = []
        for pred in self.graph.predecessors(movie_node):
            if self.node_types.get(pred) == "director":
                directors.append(pred)
        return directors

    def get_movies_with_actor_pair(self, actor1_id: int, actor2_id: int) -> List[str]:
        """Find movies where two actors have worked together."""
        actor1_movies = set(self.get_actor_movies(actor1_id))
        actor2_movies = set(self.get_actor_movies(actor2_id))
        return list(actor1_movies & actor2_movies)

    def get_shortest_path(self, source_id: int, target_id: int, source_type: str, target_type: str) -> List[str]:
        """Find shortest path between two nodes (e.g., actor to movie)."""
        source_node = f"{source_type}_{source_id}"
        target_node = f"{target_type}_{target_id}"
        try:
            return nx.shortest_path(self.graph, source_node, target_node)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def get_graph_stats(self) -> Dict:
        """Get statistics about the knowledge graph."""
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
        }
