"""Fetch movie data from OMDB API."""
import requests
import logging
from typing import List, Dict, Optional
from backend.config import settings

logger = logging.getLogger(__name__)


class OmdbFetcher:
    """Fetch data from OMDB API."""

    BASE_URL = "https://www.omdbapi.com/"

    def __init__(self):
        self.api_key = settings.omdb_api_key
        self.timeout = settings.api_timeout
        if not self.api_key:
            raise ValueError("OMDB_API_KEY not set in environment")

    def _make_request(self, params: Dict) -> Dict:
        """Make a request to OMDB API."""
        default_params = {"apikey": self.api_key}
        if params:
            default_params.update(params)

        try:
            response = requests.get(self.BASE_URL, params=default_params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {}

    def search_movies(self, search_query: str, page: int = 1) -> List[Dict]:
        """Search for movies by title (returns list of movie search results)."""
        params = {"s": search_query, "type": "movie", "page": page}
        data = self._make_request(params)
        
        if data.get("Response") == "True":
            return data.get("Search", [])
        else:
            logger.warning(f"Search failed: {data.get('Error')}")
            return []

    def get_movie_details(self, imdb_id: str) -> Dict:
        """Get detailed information about a specific movie using IMDB ID."""
        params = {"i": imdb_id, "plot": "full"}
        return self._make_request(params)

    def get_movie_by_title(self, title: str, year: Optional[str] = None) -> Dict:
        """Get movie details by title and optional year."""
        params = {"t": title, "plot": "full"}
        if year:
            params["y"] = year
        return self._make_request(params)
