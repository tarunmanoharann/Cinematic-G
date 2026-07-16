"""ETL pipeline orchestration."""
import asyncio
import logging
from typing import List, Dict
from backend.etl.tmdb_fetcher import TMDbFetcher
from backend.etl.processor import MovieProcessor
from backend.etl.graph_builder import KnowledgeGraphBuilder
from backend.db.mongo import db_manager
from backend.config import settings

logger = logging.getLogger(__name__)


class ETLPipeline:
    """Main ETL pipeline for movie data."""

    def __init__(self):
        self.fetcher = TMDbFetcher()
        self.processor = MovieProcessor()
        self.graph = KnowledgeGraphBuilder()

    async def fetch_and_process_movies(self, pages: int = 5) -> List[Dict]:
        """Fetch movies from TMDb and process them."""
        all_movies = []

        logger.info(f"Fetching movies from {pages} pages...")
        for page in range(1, pages + 1):
            movies = self.fetcher.get_popular_movies(page=page)
            logger.info(f"Fetched {len(movies)} movies from page {page}")
            all_movies.extend(movies)

        logger.info(f"Total movies fetched: {len(all_movies)}")
        return all_movies

    async def enrich_movie_data(self, movies: List[Dict]) -> List[Dict]:
        """Add detailed information to movies."""
        enriched_movies = []

        for i, movie in enumerate(movies):
            try:
                movie_id = movie["id"]
                details = self.fetcher.get_movie_details(movie_id)

                # Merge basic and detailed info
                enriched = {**movie, **details}
                enriched["tmdb_id"] = movie_id
                enriched_movies.append(enriched)

                if (i + 1) % 10 == 0:
                    logger.info(f"Enriched {i + 1}/{len(movies)} movies")
                    await asyncio.sleep(0.25)  # Rate limiting

            except Exception as e:
                logger.error(f"Error enriching movie {movie_id}: {e}")
                continue

        return enriched_movies

    async def load_movies_to_db(self, movies: List[Dict]):
        """Store movies in MongoDB."""
        logger.info(f"Loading {len(movies)} movies to MongoDB...")

        for i, movie in enumerate(movies):
            try:
                # Clean up the data
                movie_doc = {
                    "tmdb_id": movie.get("id") or movie.get("tmdb_id"),
                    "title": movie.get("title", ""),
                    "overview": movie.get("overview", ""),
                    "release_date": movie.get("release_date"),
                    "poster_path": movie.get("poster_path"),
                    "vote_average": movie.get("vote_average", 0),
                    "vote_count": movie.get("vote_count", 0),
                    "popularity": movie.get("popularity", 0),
                    "runtime": movie.get("runtime"),
                    "revenue": movie.get("revenue"),
                    "budget": movie.get("budget"),
                    "genres": movie.get("genres", []),
                    "cast": movie.get("cast", []),
                    "crew": movie.get("crew", []),
                }

                await db_manager.insert_movie(movie_doc)

                if (i + 1) % 10 == 0:
                    logger.info(f"Loaded {i + 1}/{len(movies)} movies")

            except Exception as e:
                logger.error(f"Error loading movie: {e}")
                continue

    async def build_knowledge_graph(self, movies: List[Dict]):
        """Build knowledge graph from movie data."""
        logger.info("Building knowledge graph...")

        genres_cache = {}  # Cache for genres

        for i, movie in enumerate(movies):
            try:
                movie_id = movie.get("id") or movie.get("tmdb_id")

                # Add movie node
                self.graph.add_movie(
                    movie_id,
                    movie.get("title", ""),
                    rating=movie.get("vote_average", 0),
                    popularity=movie.get("popularity", 0),
                )

                # Add genres
                for genre in movie.get("genres", []):
                    genre_id = genre.get("id")
                    if genre_id not in genres_cache:
                        self.graph.add_genre(genre_id, genre.get("name", ""))
                        genres_cache[genre_id] = True
                    self.graph.add_genre_to_movie(genre_id, movie_id)

                # Add cast
                for actor in movie.get("cast", [])[:10]:  # Top 10 actors
                    actor_id = actor.get("id")
                    if actor_id:
                        self.graph.add_actor(actor_id, actor.get("name", ""))
                        self.graph.add_actor_to_movie(actor_id, movie_id, actor.get("character", ""))

                # Add directors
                for crew in movie.get("crew", []):
                    if crew.get("job") == "Director":
                        director_id = crew.get("id")
                        if director_id:
                            self.graph.add_director(director_id, crew.get("name", ""))
                            self.graph.add_director_to_movie(director_id, movie_id)

                if (i + 1) % 20 == 0:
                    logger.info(f"Added {i + 1}/{len(movies)} movies to graph")

            except Exception as e:
                logger.error(f"Error building graph for movie: {e}")
                continue

        stats = self.graph.get_graph_stats()
        logger.info(f"Knowledge graph stats: {stats}")

    async def run(self, num_pages: int = 5):
        """Run the complete ETL pipeline."""
        try:
            logger.info("Starting ETL pipeline...")

            # Connect to MongoDB
            await db_manager.connect()
            await db_manager.create_indexes()

            # Fetch and process
            movies = await self.fetch_and_process_movies(pages=num_pages)
            enriched_movies = await self.enrich_movie_data(movies)

            # Load to MongoDB
            await self.load_movies_to_db(enriched_movies)

            # Build knowledge graph
            await self.build_knowledge_graph(enriched_movies)

            # Process for recommendations
            movies_df = self.processor.process_movie_data(enriched_movies)
            self.processor.build_tfidf_matrix(movies_df)

            logger.info("ETL pipeline completed successfully")
            return True

        except Exception as e:
            logger.error(f"ETL pipeline failed: {e}")
            return False
        finally:
            await db_manager.disconnect()


async def main():
    """Run ETL pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    pipeline = ETLPipeline()
    await pipeline.run(num_pages=5)


if __name__ == "__main__":
    asyncio.run(main())
