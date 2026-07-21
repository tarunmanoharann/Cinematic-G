"""Streamlit dashboard for CineGraph movie recommendation system."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
from backend.config import settings
import logging

logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="CineGraph - Movie Analytics",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main {
        padding-top: 2rem;
    }
    h1 {
        color: #FF6B6B;
        font-size: 2.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_mongo_connection():
    """Connect to MongoDB."""
    try:
        client = MongoClient(settings.mongodb_url)
        db = client[settings.mongodb_db_name]
        # Test connection
        client.server_info()
        return db
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        return None


@st.cache_data
def load_movies_data():
    """Load all movies from MongoDB."""
    db = get_mongo_connection()
    if db is None:
        return None

    try:
        movies_collection = db["movies"]
        movies = list(movies_collection.find({}, {"_id": 0}))
        if not movies:
            st.warning("No movies found in database. Please run the ETL pipeline first.")
            return None

        df = pd.DataFrame(movies)

        # Ensure required columns exist and process data
        required_columns = ["title", "imdb_rating", "metascore", "imdb_votes", "year", "plot"]
        for col in required_columns:
            if col not in df.columns:
                if col == "imdb_rating":
                    df[col] = 0.0
                elif col == "year":
                    df[col] = None
                else:
                    df[col] = "N/A"
            else:
                if col == "imdb_rating":
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
                elif col == "year":
                    # Don't fillna here - the year column is parsed/normalized
                    # into an int-or-None a few lines below. Calling
                    # fillna(None) is invalid in modern pandas and raises
                    # "Must specify a fill 'value' or 'method'."
                    pass
                else:
                    df[col] = df[col].fillna("N/A")

        # Process year field (since it's stored as string like "2000" or "2000–2001")
        if "year" in df.columns:
            df["year"] = df["year"].apply(
                lambda x: int(x[:4]) if pd.notna(x) and str(x).strip() != "" and str(x).strip() != "N/A" else None
            )

        # Extract genres
        if "genres" in df.columns:
            df["genre_list"] = df["genres"].apply(
                lambda x: [g["name"] for g in x] if isinstance(x, list) else []
            )
        else:
            df["genre_list"] = [[] for _ in range(len(df))]

        return df
    except Exception as e:
        st.error(f"Error loading movies: {e}")
        return None


def display_header():
    """Display app header."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🎬 CineGraph")
        st.subheader("Movie Analytics & Recommendation Engine")
    with col2:
        st.metric("Version", "1.0")


def display_overview(df: pd.DataFrame):
    """Display key metrics."""
    st.header("📊 Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Movies", len(df))
    with col2:
        avg_rating = df["imdb_rating"].mean()
        st.metric("Avg Rating", f"{avg_rating:.1f}/10")
    with col3:
        avg_metascore = df["metascore"].apply(lambda x: float(x) if pd.notna(x) and x != "N/A" else 0).mean()
        st.metric("Avg Metascore", f"{avg_metascore:.0f}")
    with col4:
        if "year" in df.columns and df["year"].notna().any():
            year_range = f"{int(df['year'].min())} - {int(df['year'].max())}"
        else:
            year_range = "N/A"
        st.metric("Year Range", year_range)


def display_rating_distribution(df: pd.DataFrame):
    """Display rating distribution chart."""
    st.subheader("Rating Distribution")

    # Create bins for ratings
    bins = [0, 2, 4, 6, 8, 10]
    labels = ["0-2", "2-4", "4-6", "6-8", "8-10"]
    df["rating_bin"] = pd.cut(df["imdb_rating"], bins=bins, labels=labels, right=False)
    rating_counts = df["rating_bin"].value_counts().sort_index()

    fig = px.bar(
        x=rating_counts.index,
        y=rating_counts.values,
        labels={"x": "Rating Range", "y": "Number of Movies"},
        color=rating_counts.values,
        color_continuous_scale="Viridis",
    )
    st.plotly_chart(fig, use_container_width=True)


def display_popularity_trends(df: pd.DataFrame):
    """Display popularity trends over years."""
    st.subheader("Rating Trends by Year")

    if "year" in df.columns and df["year"].notna().any():
        yearly_data = (
            df[df["year"].notna()]
            .groupby("year")["imdb_rating"]
            .agg(["mean", "count"])
            .reset_index()
        )

        fig = px.line(
            yearly_data,
            x="year",
            y="mean",
            markers=True,
            labels={"mean": "Avg Rating", "year": "Year"},
            title="Average Rating by Release Year",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No year data available")


def display_top_movies(df: pd.DataFrame):
    """Display top-rated movies."""
    st.subheader("🏆 Top-Rated Movies")

    n_movies = st.slider("Number of movies to display", 5, 20, 10)
    sort_by = st.selectbox("Sort by", ["imdb_rating", "metascore", "imdb_votes"])

    # Process numeric columns for sorting
    df_sorted = df.copy()
    df_sorted["metascore_num"] = df_sorted["metascore"].apply(lambda x: float(x) if pd.notna(x) and x != "N/A" else 0)
    df_sorted["imdb_votes_num"] = df_sorted["imdb_votes"].apply(lambda x: int(x.replace(",", "")) if pd.notna(x) and x != "N/A" else 0)

    sort_col = sort_by
    if sort_by == "metascore":
        sort_col = "metascore_num"
    elif sort_by == "imdb_votes":
        sort_col = "imdb_votes_num"

    top_movies = df_sorted.nlargest(n_movies, sort_col)[["title", "imdb_rating", "metascore", "year"]]

    st.dataframe(top_movies, use_container_width=True)


def display_genre_analysis(df: pd.DataFrame):
    """Display genre analysis."""
    st.subheader("📁 Genre Analysis")

    # Flatten genres
    all_genres = []
    for genres in df["genre_list"]:
        all_genres.extend(genres)

    if not all_genres:
        st.info("No genre data available")
        return

    genre_counts = pd.Series(all_genres).value_counts()

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            x=genre_counts.values,
            y=genre_counts.index,
            orientation="h",
            labels={"x": "Number of Movies", "y": "Genre"},
            color=genre_counts.values,
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.pie(
            values=genre_counts.values,
            names=genre_counts.index,
            title="Genre Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)


def display_filters(df: pd.DataFrame):
    """Display filter options and filtered results."""
    st.header("🔍 Filter & Search")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Genre filter
        all_genres = []
        for genres in df["genre_list"]:
            all_genres.extend(genres)
        unique_genres = sorted(list(set(all_genres)))

        selected_genres = st.multiselect("Select Genres", unique_genres)

    with col2:
        # Rating filter
        min_rating, max_rating = st.slider(
            "Rating Range", 0.0, 10.0, (0.0, 10.0), step=0.5
        )

    with col3:
        # Year filter
        if "year" in df.columns and df["year"].notna().any():
            min_year = int(df["year"].min())
            max_year = int(df["year"].max())
            selected_years = st.slider(
                "Year Range", min_year, max_year, (min_year, max_year)
            )
        else:
            selected_years = (None, None)

    # Apply filters
    filtered_df = df.copy()

    if selected_genres:
        filtered_df = filtered_df[
            filtered_df["genre_list"].apply(
                lambda x: any(g in selected_genres for g in x)
            )
        ]

    filtered_df = filtered_df[
        (filtered_df["imdb_rating"] >= min_rating)
        & (filtered_df["imdb_rating"] <= max_rating)
    ]

    if selected_years[0] and "year" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["year"] >= selected_years[0])
            & (filtered_df["year"] <= selected_years[1])
        ]

    st.subheader(f"Found {len(filtered_df)} movies")

    # Display filtered results
    if not filtered_df.empty:
        display_cols = ["title", "imdb_rating", "metascore", "year"]
        display_cols = [col for col in display_cols if col in filtered_df.columns]
        st.dataframe(filtered_df[display_cols], use_container_width=True)
    else:
        st.info("No movies match your filters")


def display_search(df: pd.DataFrame):
    """Display search functionality."""
    st.header("🔎 Search Movies")

    search_query = st.text_input("Enter movie title or keywords")

    if search_query:
        search_results = df[
            df["title"].str.contains(search_query, case=False, na=False)
        ]

        if not search_results.empty:
            st.subheader(f"Found {len(search_results)} movie(s)")
            for _, movie in search_results.head(10).iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{movie['title']}**")
                    st.write(movie["plot"][:200] + "...")
                with col2:
                    st.metric("Rating", f"{movie['imdb_rating']:.1f}/10")
        else:
            st.info("No movies found matching your search")


def main():
    """Main app function."""
    display_header()

    # Load data
    df = load_movies_data()

    if df is None or len(df) == 0:
        st.error("No data available. Please run the ETL pipeline first.")
        st.info(
            "Run this command in your backend folder:\n"
            "`python -m backend.etl.pipeline`"
        )
        return

    # Display tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Overview", "Analysis", "Top Movies", "Filter", "Search"]
    )

    with tab1:
        display_overview(df)

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            display_rating_distribution(df)
        with col2:
            display_popularity_trends(df)

        display_genre_analysis(df)

    with tab3:
        display_top_movies(df)

    with tab4:
        display_filters(df)

    with tab5:
        display_search(df)

    # Footer
    st.divider()
    st.markdown(
        "Built with ❤️ using Streamlit, Plotly, and MongoDB | CineGraph 2024"
    )


if __name__ == "__main__":
    main()