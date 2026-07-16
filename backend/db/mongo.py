"""MongoDB connection and operations."""
from motor.motor_asyncio import AsyncClient, AsyncDatabase
from pymongo import ASCENDING, TEXT
from backend.config import settings
import logging

logger = logging.getLogger(__name__)


class MongoDBManager:
    """Manage MongoDB connections and operations."""

    def __init__(self):
        self.client: AsyncClient = None
        self.db: AsyncDatabase = None

    async def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = AsyncClient(settings.mongodb_url)
            self.db = self.client[settings.mongodb_db_name]
            await self.client.server_info()  # Test connection
            logger.info("Connected to MongoDB successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def create_indexes(self):
        """Create necessary indexes for collections."""
        # Movies collection indexes
        movies = self.db["movies"]
        await movies.create_index([("tmdb_id", ASCENDING)], unique=True)
        await movies.create_index([("title", TEXT)])
        await movies.create_index([("genres.id", ASCENDING)])
        await movies.create_index([("release_date", ASCENDING)])
        await movies.create_index([("vote_average", ASCENDING)])

        # Actors collection indexes
        actors = self.db["actors"]
        await actors.create_index([("tmdb_id", ASCENDING)], unique=True)
        await actors.create_index([("name", TEXT)])

        # Directors collection indexes
        directors = self.db["directors"]
        await directors.create_index([("tmdb_id", ASCENDING)], unique=True)
        await directors.create_index([("name", TEXT)])

        logger.info("Created MongoDB indexes")

    async def insert_movie(self, movie_data: dict):
        """Insert or update a movie document."""
        movies = self.db["movies"]
        await movies.update_one(
            {"tmdb_id": movie_data["tmdb_id"]},
            {"$set": movie_data},
            upsert=True,
        )

    async def insert_actor(self, actor_data: dict):
        """Insert or update an actor document."""
        actors = self.db["actors"]
        await actors.update_one(
            {"tmdb_id": actor_data["tmdb_id"]},
            {"$set": actor_data},
            upsert=True,
        )

    async def insert_director(self, director_data: dict):
        """Insert or update a director document."""
        directors = self.db["directors"]
        await directors.update_one(
            {"tmdb_id": director_data["tmdb_id"]},
            {"$set": director_data},
            upsert=True,
        )

    async def get_movies(self, limit: int = 100, skip: int = 0):
        """Get paginated list of movies."""
        movies = self.db["movies"]
        return await movies.find({}).skip(skip).limit(limit).to_list(None)

    async def get_movie_by_tmdb_id(self, tmdb_id: int):
        """Get a single movie by TMDB ID."""
        movies = self.db["movies"]
        return await movies.find_one({"tmdb_id": tmdb_id})

    async def get_movies_by_genre(self, genre_id: int):
        """Get all movies with a specific genre."""
        movies = self.db["movies"]
        return await movies.find({"genres.id": genre_id}).to_list(None)

    async def get_movies_by_actor(self, actor_name: str):
        """Get all movies with a specific actor."""
        movies = self.db["movies"]
        return await movies.find({"cast.name": actor_name}).to_list(None)

    async def get_movies_by_director(self, director_name: str):
        """Get all movies by a specific director."""
        movies = self.db["movies"]
        return await movies.find({"crew.name": director_name, "crew.job": "Director"}).to_list(None)

    async def get_actor(self, tmdb_id: int):
        """Get actor details by TMDB ID."""
        actors = self.db["actors"]
        return await actors.find_one({"tmdb_id": tmdb_id})

    async def get_director(self, tmdb_id: int):
        """Get director details by TMDB ID."""
        directors = self.db["directors"]
        return await directors.find_one({"tmdb_id": tmdb_id})

    async def get_collection_count(self, collection_name: str):
        """Get count of documents in a collection."""
        collection = self.db[collection_name]
        return await collection.count_documents({})


# Global MongoDB manager instance
db_manager = MongoDBManager()
