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
        # Ensure all movies have required fields
        safe_movies = []
        for movie in movies:
            safe_movie = movie.copy()
            # Use Title (OMDB) or title
            safe_movie["title"] = safe_movie.get("Title") or safe_movie.get("title", "")
            safe_movie["plot"] = safe_movie.get("plot") or safe_movie.get("Plot", "")
            safe_movies.append(safe_movie)
        
        df = pd.DataFrame(safe_movies)

        # Fill missing values
        if "plot" in df.columns:
            df["plot"] = df["plot"].fillna("")
        else:
            df["plot"] = ""
            
        if "title" in df.columns:
            df["title"] = df["title"].fillna("")
        else:
            df["title"] = ""
        
        # Create genre string for TF-IDF
        df["genre_string"] = df.get("genres", pd.Series([[] for _ in range(len(df))])).apply(
            lambda x: " ".join([g.get("name", "") for g in x]) if isinstance(x, list) else ""
        )

        # Combine features for content similarity
        df["content"] = (
            df["plot"] + " " + df["genre_string"] + " " + df["title"]
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
            (self.movies_df["imdb_rating"] >= min_rating)
            & (self.movies_df["imdb_rating"] <= max_rating)
        ]

    def get_movies_by_year(self, year: str) -> pd.DataFrame:
        """Filter movies by release year."""
        return self.movies_df[self.movies_df["year"] == str(year)]

    def get_movies_by_genre(self, genre_name: str) -> pd.DataFrame:
        """Filter movies by genre."""
        return self.movies_df[
            self.movies_df["genre_string"].str.contains(genre_name, case=False, na=False)
        ]

    def get_top_movies(self, n: int = 10, sort_by: str = "imdb_rating") -> pd.DataFrame:
        """Get top N movies sorted by a column."""
        return self.movies_df.nlargest(n, sort_by)

    def get_statistics(self) -> Dict:
        """Get overall statistics about movies."""
        return {
            "total_movies": len(self.movies_df),
            "avg_rating": self.movies_df["imdb_rating"].mean(),
        }
