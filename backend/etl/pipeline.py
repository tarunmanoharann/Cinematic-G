"""ETL pipeline orchestration."""
import asyncio
import logging
from typing import List, Dict
from backend.etl.omdb_fetcher import OmdbFetcher
from backend.etl.processor import MovieProcessor
from backend.etl.graph_builder import KnowledgeGraphBuilder
from backend.db.mongo import db_manager
from backend.config import settings

logger = logging.getLogger(__name__)


class ETLPipeline:
    """Main ETL pipeline for movie data."""

    def __init__(self):
        self.fetcher = OmdbFetcher()
        self.processor = MovieProcessor()
        self.graph = KnowledgeGraphBuilder()
        
        # Common movie search queries to get initial movie list (OMDB doesn't have a "popular movies" endpoint)
        self.search_queries = [
            "Batman", "Superman", "Star Wars", "Harry Potter", "Marvel",
            "Inception", "The Matrix", "Interstellar", "Avatar", "Titanic",
            "Jurassic Park", "The Godfather", "Forrest Gump", "Fight Club",
            "Pulp Fiction", "The Shawshank Redemption", "The Dark Knight",
            "Inception", "Gladiator", "Saving Private Ryan"
        ]

    async def fetch_and_process_movies(self, pages_per_query: int = 1) -> List[Dict]:
        """Fetch movies from OMDB using search queries and process them."""
        all_movies = []
        seen_imdb_ids = set()

        logger.info(f"Fetching movies from {len(self.search_queries)} search queries...")
        for query in self.search_queries:
            for page in range(1, pages_per_query + 1):
                search_results = self.fetcher.search_movies(query, page=page)
                logger.info(f"Fetched {len(search_results)} movies for query '{query}' (page {page})")
                
                for movie in search_results:
                    imdb_id = movie.get("imdbID")
                    if imdb_id and imdb_id not in seen_imdb_ids:
                        seen_imdb_ids.add(imdb_id)
                        all_movies.append(movie)
                
                await asyncio.sleep(0.25)  # Rate limiting
                
                if len(all_movies) >= settings.max_movies_fetch:
                    break
            if len(all_movies) >= settings.max_movies_fetch:
                break

        logger.info(f"Total unique movies fetched: {len(all_movies)}")
        return all_movies

    async def enrich_movie_data(self, movies: List[Dict]) -> List[Dict]:
        """Add detailed information to movies."""
        enriched_movies = []

        for i, movie in enumerate(movies):
            try:
                imdb_id = movie["imdbID"]
                details = self.fetcher.get_movie_details(imdb_id)

                if details.get("Response") == "True":
                    enriched = {**movie, **details}
                    enriched["imdb_id"] = imdb_id
                    
                    # Process genres into list
                    genre_str = details.get("Genre", "")
                    enriched["genres"] = [{"name": g.strip()} for g in genre_str.split(",") if g.strip()]
                    
                    # Process actors into list
                    actors_str = details.get("Actors", "")
                    enriched["actors"] = [{"name": a.strip()} for a in actors_str.split(",") if a.strip()]
                    
                    # Process directors into list
                    director_str = details.get("Director", "")
                    enriched["directors"] = [{"name": d.strip()} for d in director_str.split(",") if d.strip()]
                    
                    # Convert imdbRating to float
                    try:
                        enriched["imdb_rating"] = float(details.get("imdbRating", "0"))
                    except (ValueError, TypeError):
                        enriched["imdb_rating"] = 0.0
                        
                    enriched["imdb_votes"] = details.get("imdbVotes", "0")
                    enriched["plot"] = details.get("Plot", "")
                    enriched["poster"] = details.get("Poster", "")
                    
                    enriched_movies.append(enriched)

                if (i + 1) % 10 == 0:
                    logger.info(f"Enriched {i + 1}/{len(movies)} movies")
                    await asyncio.sleep(0.25)  # Rate limiting

            except Exception as e:
                logger.error(f"Error enriching movie {movie.get('imdbID', 'unknown')}: {e}")
                continue

        return enriched_movies

    async def load_movies_to_db(self, movies: List[Dict]):
        """Store movies in MongoDB."""
        logger.info(f"Loading {len(movies)} movies to MongoDB...")

        for i, movie in enumerate(movies):
            try:
                # Clean up the data
                movie_doc = {
                    "imdb_id": movie.get("imdb_id"),
                    "title": movie.get("Title", ""),
                    "plot": movie.get("plot", ""),
                    "year": movie.get("Year"),
                    "runtime": movie.get("Runtime"),
                    "imdb_rating": movie.get("imdb_rating", 0.0),
                    "imdb_votes": movie.get("imdb_votes", "0"),
                    "poster": movie.get("poster"),
                    "genres": movie.get("genres", []),
                    "actors": movie.get("actors", []),
                    "directors": movie.get("directors", []),
                    "rated": movie.get("Rated"),
                    "released": movie.get("Released"),
                    "writer": movie.get("Writer"),
                    "movie_languages": movie.get("Language"),  # Rename to avoid MongoDB reserved field
                    "country": movie.get("Country"),
                    "awards": movie.get("Awards"),
                    "metascore": movie.get("Metascore"),
                    "box_office": movie.get("BoxOffice"),
                    "production": movie.get("Production"),
                    "website": movie.get("Website"),
                    "dvd": movie.get("DVD"),
                }

                await db_manager.insert_movie(movie_doc)

                if (i + 1) % 10 == 0:
                    logger.info(f"Loaded {i + 1}/{len(movies)} movies")

            except Exception as e:
                logger.error(f"Error loading movie {movie.get('imdb_id', 'unknown')}: {e}")
                continue

    async def build_knowledge_graph(self, movies: List[Dict]):
        """Build knowledge graph from movie data."""
        logger.info("Building knowledge graph...")

        genres_cache = {}  # Cache for genres (use name as id for OMDB)
        actor_id_counter = 1
        director_id_counter = 1
        genre_id_counter = 1

        for i, movie in enumerate(movies):
            try:
                imdb_id = movie.get("imdb_id")
                movie_id = imdb_id  # Use imdb_id as movie node id

                # Add movie node
                self.graph.add_movie(
                    movie_id,
                    movie.get("Title", ""),
                    rating=movie.get("imdb_rating", 0),
                )

                # Add genres
                for genre in movie.get("genres", []):
                    genre_name = genre.get("name")
                    if genre_name and genre_name not in genres_cache:
                        self.graph.add_genre(genre_id_counter, genre_name)
                        genres_cache[genre_name] = genre_id_counter
                        genre_id_counter += 1
                    if genre_name in genres_cache:
                        self.graph.add_genre_to_movie(genres_cache[genre_name], movie_id)

                # Add cast (actors)
                for actor in movie.get("actors", [])[:10]:  # Top 10 actors
                    actor_name = actor.get("name")
                    if actor_name:
                        self.graph.add_actor(actor_id_counter, actor_name)
                        self.graph.add_actor_to_movie(actor_id_counter, movie_id, "")
                        actor_id_counter += 1

                # Add directors
                for director in movie.get("directors", []):
                    director_name = director.get("name")
                    if director_name:
                        self.graph.add_director(director_id_counter, director_name)
                        self.graph.add_director_to_movie(director_id_counter, movie_id)
                        director_id_counter += 1

                if (i + 1) % 20 == 0:
                    logger.info(f"Added {i + 1}/{len(movies)} movies to graph")

            except Exception as e:
                logger.error(f"Error building graph for movie: {e}")
                continue

        stats = self.graph.get_graph_stats()
        logger.info(f"Knowledge graph stats: {stats}")

    async def run(self, num_pages_per_query: int = 1):
        """Run the complete ETL pipeline."""
        try:
            logger.info("Starting ETL pipeline...")

            # Connect to MongoDB
            await db_manager.connect()
            await db_manager.create_indexes()

            # Fetch and process
            movies = await self.fetch_and_process_movies(pages_per_query=num_pages_per_query)
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
    await pipeline.run(num_pages_per_query=1)


if __name__ == "__main__":
    asyncio.run(main())
