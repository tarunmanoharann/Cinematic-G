"""Data processing for movies and recommendations."""
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class MovieProcessor:
    """Process movie data for recommendations."""

    def __init__(self):
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.movies_df = None

    def process_movie_data(self, movies: List[Dict]) -> pd.DataFrame:
        """Convert raw movie data to DataFrame with processed features."""
        df = pd.DataFrame(movies)

        # Fill missing values
        df["overview"] = df["overview"].fillna("")
        df["vote_average"] = df["vote_average"].fillna(0)
        df["popularity"] = df["popularity"].fillna(0)
        df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")

        # Extract year from release date
        df["year"] = df["release_date"].dt.year

        # Create genre string for TF-IDF
        df["genre_string"] = df["genres"].apply(
            lambda x: " ".join([g["name"] for g in x]) if isinstance(x, list) else ""
        )

        # Combine features for content similarity
        df["content"] = (
            df["overview"] + " " + df["genre_string"] + " " + df["title"]
        ).fillna("")

        logger.info(f"Processed {len(df)} movies")
        return df

    def build_tfidf_matrix(self, movies_df: pd.DataFrame):
        """Build TF-IDF matrix for content-based recommendations."""
        self.movies_df = movies_df
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000, stop_words="english", min_df=1
        )
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(
            movies_df["content"].values
        )
        logger.info("Built TF-IDF matrix")

    def get_content_based_recommendations(
        self, movie_title: str, n_recommendations: int = 10
    ) -> List[Dict]:
        """Get content-based recommendations for a movie."""
        if self.tfidf_matrix is None:
            logger.error("TF-IDF matrix not built. Call build_tfidf_matrix first.")
            return []

        try:
            # Find the movie index
            movie_idx = self.movies_df[self.movies_df["title"].str.lower() == movie_title.lower()].index[0]
        except IndexError:
            logger.warning(f"Movie '{movie_title}' not found")
            return []

        # Compute similarity scores
        similarity_scores = cosine_similarity(
            self.tfidf_matrix[movie_idx], self.tfidf_matrix
        )[0]

        # Get top N recommendations (excluding the movie itself)
        similar_indices = similarity_scores.argsort()[::-1][1 : n_recommendations + 1]

        recommendations = self.movies_df.iloc[similar_indices].to_dict(orient="records")
        return recommendations

    def get_movies_by_rating_range(
        self, min_rating: float = 0, max_rating: float = 10
    ) -> pd.DataFrame:
        """Filter movies by rating range."""
        return self.movies_df[
            (self.movies_df["vote_average"] >= min_rating)
            & (self.movies_df["vote_average"] <= max_rating)
        ]

    def get_movies_by_year(self, year: int) -> pd.DataFrame:
        """Filter movies by release year."""
        return self.movies_df[self.movies_df["year"] == year]

    def get_movies_by_genre(self, genre_name: str) -> pd.DataFrame:
        """Filter movies by genre."""
        return self.movies_df[
            self.movies_df["genre_string"].str.contains(genre_name, case=False, na=False)
        ]

    def get_top_movies(self, n: int = 10, sort_by: str = "vote_average") -> pd.DataFrame:
        """Get top N movies sorted by a column."""
        return self.movies_df.nlargest(n, sort_by)

    def get_statistics(self) -> Dict:
        """Get overall statistics about movies."""
        return {
            "total_movies": len(self.movies_df),
            "avg_rating": self.movies_df["vote_average"].mean(),
            "avg_popularity": self.movies_df["popularity"].mean(),
            "year_range": (self.movies_df["year"].min(), self.movies_df["year"].max()),
        }
