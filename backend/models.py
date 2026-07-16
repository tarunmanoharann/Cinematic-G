"""Pydantic models for data validation."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MovieBase(BaseModel):
    """Base model for movie data."""

    tmdb_id: int
    title: str
    overview: str = ""
    release_date: Optional[str] = None
    runtime: Optional[int] = None
    vote_average: float = 0.0
    vote_count: int = 0
    popularity: float = 0.0
    poster_path: Optional[str] = None


class GenreData(BaseModel):
    """Genre information."""

    id: int
    name: str


class CastMember(BaseModel):
    """Cast member information."""

    tmdb_id: int
    name: str
    character: str
    profile_path: Optional[str] = None


class CrewMember(BaseModel):
    """Crew member information (director, etc)."""

    tmdb_id: int
    name: str
    job: str
    department: str


class MovieDetail(MovieBase):
    """Complete movie details."""

    genres: List[GenreData] = []
    cast: List[CastMember] = []
    crew: List[CrewMember] = []
    revenue: Optional[int] = None
    budget: Optional[int] = None
    language: Optional[str] = None
    tagline: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
