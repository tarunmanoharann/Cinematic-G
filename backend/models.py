"""Pydantic models for data validation."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MovieBase(BaseModel):
    """Base model for movie data."""

    imdb_id: str
    title: str
    plot: str = ""
    year: Optional[str] = None
    runtime: Optional[str] = None
    imdb_rating: float = 0.0
    imdb_votes: str = "0"
    poster: Optional[str] = None


class GenreData(BaseModel):
    """Genre information."""
    name: str


class ActorData(BaseModel):
    """Actor information."""
    name: str


class DirectorData(BaseModel):
    """Director information."""
    name: str


class MovieDetail(MovieBase):
    """Complete movie details."""

    genres: List[GenreData] = []
    actors: List[ActorData] = []
    directors: List[DirectorData] = []
    rated: Optional[str] = None
    released: Optional[str] = None
    writer: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    awards: Optional[str] = None
    metascore: Optional[str] = None
    box_office: Optional[str] = None
    production: Optional[str] = None
    website: Optional[str] = None
    dvd: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
