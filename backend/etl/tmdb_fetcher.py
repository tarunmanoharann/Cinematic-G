"""Fetch movie data from TMDb API."""
import requests
import logging
from typing import List, Dict, Optional
from backend.config import settings

logger = logging.getLogger(__name__)


class TMDbFetcher:
    """Fetch data from The Movie Database API."""

    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self):
        self.api_key = settings.tmdb_api_key
        self.timeout = settings.api_timeout
        if not self.api_key:
            raise ValueError("TMDB_API_KEY not set in environment")

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to TMDb API."""
        url = f"{self.BASE_URL}{endpoint}"
        default_params = {"api_key": self.api_key, "language": "en-US"}
        if params:
            default_params.update(params)

        try:
            response = requests.get(url, params=default_params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {}

    def get_popular_movies(self, page: int = 1) -> List[Dict]:
        """Get popular movies paginated."""
        data = self._make_request("/movie/popular", {"page": page})
        return data.get("results", [])

    def get_top_rated_movies(self, page: int = 1) -> List[Dict]:
        """Get top-rated movies paginated."""
        data = self._make_request("/movie/top_rated", {"page": page})
        return data.get("results", [])

    def get_movie_details(self, movie_id: int) -> Dict:
        """Get detailed information about a specific movie."""
        endpoint = f"/movie/{movie_id}"
        params = {"append_to_response": "credits,recommendations"}
        return self._make_request(endpoint, params)

    def get_movie_credits(self, movie_id: int) -> Dict:
        """Get cast and crew for a movie."""
        return self._make_request(f"/movie/{movie_id}/credits")

    def search_movies(self, query: str, page: int = 1) -> List[Dict]:
        """Search for movies by title."""
        data = self._make_request("/search/movie", {"query": query, "page": page})
        return data.get("results", [])

    def get_genres(self) -> List[Dict]:
        """Get all available genres."""
        data = self._make_request("/genre/movie/list")
        return data.get("genres", [])

    def get_movies_by_genre(self, genre_id: int, page: int = 1) -> List[Dict]:
        """Get movies filtered by genre."""
        data = self._make_request("/discover/movie", {"with_genres": genre_id, "page": page})
        return data.get("results", [])

    def get_actor_details(self, actor_id: int) -> Dict:
        """Get detailed information about an actor."""
        return self._make_request(f"/person/{actor_id}")

    def get_actor_movies(self, actor_id: int) -> List[Dict]:
        """Get all movies for an actor."""
        data = self._make_request(f"/person/{actor_id}/movie_credits")
        return data.get("cast", [])
