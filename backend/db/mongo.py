"""MongoDB connection and operations."""

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, TEXT

from backend.config import settings

logger = logging.getLogger(__name__)


class MongoDBManager:
    """Manage MongoDB connections and operations."""

    def __init__(self):
        self.client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None

    async def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.db = self.client[settings.mongodb_db_name]

            # Test the connection
            await self.client.admin.command("ping")

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

        movies = self.db["movies"]
        await movies.create_index([("imdb_id", ASCENDING)], unique=True)
        await movies.create_index([("title", TEXT)])
        await movies.create_index([("genres.name", ASCENDING)])
        await movies.create_index([("year", ASCENDING)])
        await movies.create_index([("imdb_rating", ASCENDING)])

        actors = self.db["actors"]
        await actors.create_index([("name", ASCENDING)], unique=True)
        await actors.create_index([("name", TEXT)])

        directors = self.db["directors"]
        await directors.create_index([("name", ASCENDING)], unique=True)
        await directors.create_index([("name", TEXT)])

        logger.info("Created MongoDB indexes")

    async def insert_movie(self, movie_data: dict):
        """Insert or update a movie document."""
        movies = self.db["movies"]

        await movies.update_one(
            {"imdb_id": movie_data["imdb_id"]},
            {"$set": movie_data},
            upsert=True,
        )

    async def insert_actor(self, actor_data: dict):
        """Insert or update an actor document."""
        actors = self.db["actors"]

        await actors.update_one(
            {"name": actor_data["name"]},
            {"$set": actor_data},
            upsert=True,
        )

    async def insert_director(self, director_data: dict):
        """Insert or update a director document."""
        directors = self.db["directors"]

        await directors.update_one(
            {"name": director_data["name"]},
            {"$set": director_data},
            upsert=True,
        )

    async def get_movies(self, limit: int = 100, skip: int = 0):
        """Get paginated list of movies."""
        movies = self.db["movies"]
        return await movies.find({}).skip(skip).limit(limit).to_list(length=limit)

    async def get_movie_by_imdb_id(self, imdb_id: str):
        """Get a single movie by IMDb ID."""
        movies = self.db["movies"]
        return await movies.find_one({"imdb_id": imdb_id})

    async def get_movies_by_genre(self, genre_name: str):
        """Get all movies with a specific genre."""
        movies = self.db["movies"]
        return await movies.find({"genres.name": genre_name}).to_list(length=None)

    async def get_movies_by_actor(self, actor_name: str):
        """Get all movies with a specific actor."""
        movies = self.db["movies"]
        return await movies.find({"actors.name": actor_name}).to_list(length=None)

    async def get_movies_by_director(self, director_name: str):
        """Get all movies by a specific director."""
        movies = self.db["movies"]
        return await movies.find({"directors.name": director_name}).to_list(length=None)

    async def get_actor(self, name: str):
        """Get actor details by name."""
        actors = self.db["actors"]
        return await actors.find_one({"name": name})

    async def get_director(self, name: str):
        """Get director details by name."""
        directors = self.db["directors"]
        return await directors.find_one({"name": name})

    async def get_collection_count(self, collection_name: str):
        """Get count of documents in a collection."""
        collection = self.db[collection_name]
        return await collection.count_documents({})


# Global MongoDB manager instance
db_manager = MongoDBManager()