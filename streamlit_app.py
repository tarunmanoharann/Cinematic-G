"""Streamlit dashboard for Cinematic-G movie recommendation system."""
import math

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
    page_title="Cinematic-G - Movie Analytics",
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

        # Pre-compute numeric helper columns used for sorting/filtering
        df["metascore_num"] = df["metascore"].apply(
            lambda x: float(x) if pd.notna(x) and x != "N/A" else 0.0
        )
        df["imdb_votes_num"] = df["imdb_votes"].apply(
            lambda x: int(str(x).replace(",", "")) if pd.notna(x) and x != "N/A" and str(x).strip() != "" else 0
        )

        return df
    except Exception as e:
        st.error(f"Error loading movies: {e}")
        return None


def display_header():
    """Display app header."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Cinematic-G")
    with col2:
        st.metric("Version", "1.0")


def display_overview_metrics(df: pd.DataFrame):
    """Display key metrics."""
    st.header("📊 Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Movies", len(df))
    with col2:
        avg_rating = df["imdb_rating"].mean()
        st.metric("Avg Rating", f"{avg_rating:.1f}/10")
    with col3:
        avg_metascore = df["metascore_num"].mean()
        st.metric("Avg Metascore", f"{avg_metascore:.0f}")
    with col4:
        if "year" in df.columns and df["year"].notna().any():
            year_range = f"{int(df['year'].min())} - {int(df['year'].max())}"
        else:
            year_range = "N/A"
        st.metric("Year Range", year_range)


def display_quick_search(df: pd.DataFrame):
    """Quick search box shown right on the Overview tab."""
    st.subheader("🔎 Quick Search")

    search_query = st.text_input("Enter movie title or keywords", key="overview_search")

    if search_query:
        search_results = df[
            df["title"].str.contains(search_query, case=False, na=False)
        ]

        if not search_results.empty:
            st.caption(f"Found {len(search_results)} movie(s) — showing top 10")
            for _, movie in search_results.head(10).iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{movie['title']}**")
                    plot_text = str(movie["plot"]) if pd.notna(movie["plot"]) else ""
                    st.write(plot_text[:200] + ("..." if len(plot_text) > 200 else ""))
                with col2:
                    st.metric("Rating", f"{movie['imdb_rating']:.1f}/10")
        else:
            st.info("No movies found matching your search")


def display_rating_distribution(df: pd.DataFrame):
    """Display rating distribution chart."""
    st.subheader("Rating Distribution")

    # Create bins for ratings
    bins = [0, 2, 4, 6, 8, 10]
    labels = ["0-2", "2-4", "4-6", "6-8", "8-10"]
    df = df.copy()
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


def display_overview_tab(df: pd.DataFrame):
    """Overview tab: metrics + quick search + full analysis."""
    display_overview_metrics(df)
    st.divider()
    display_quick_search(df)
    st.divider()

    st.header("📈 Analysis")
    col1, col2 = st.columns(2)
    with col1:
        display_rating_distribution(df)
    with col2:
        display_popularity_trends(df)

    display_genre_analysis(df)


def display_movies_tab(df: pd.DataFrame):
    """Movies tab: all movies with search, filters, sorting, and pagination."""
    st.header("🎞️ All Movies")

    # ---- Search ----
    search_query = st.text_input("Search by title or keywords", key="movies_search")

    # ---- Filters ----
    with st.expander("🔍 Filters", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            all_genres = []
            for genres in df["genre_list"]:
                all_genres.extend(genres)
            unique_genres = sorted(set(all_genres))
            selected_genres = st.multiselect("Genres", unique_genres, key="movies_genre_filter")

        with col2:
            min_rating, max_rating = st.slider(
                "Rating Range", 0.0, 10.0, (0.0, 10.0), step=0.5, key="movies_rating_filter"
            )

        with col3:
            if "year" in df.columns and df["year"].notna().any():
                min_year_bound = int(df["year"].min())
                max_year_bound = int(df["year"].max())
                selected_years = st.slider(
                    "Year Range",
                    min_year_bound,
                    max_year_bound,
                    (min_year_bound, max_year_bound),
                    key="movies_year_filter",
                )
            else:
                selected_years = (None, None)

    # ---- Sorting ----
    col_sort1, col_sort2 = st.columns([2, 1])
    with col_sort1:
        sort_by = st.selectbox(
            "Sort by",
            ["imdb_rating", "metascore", "imdb_votes", "title", "year"],
            key="movies_sort_by",
        )
    with col_sort2:
        sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True, key="movies_sort_order")

    sort_col_map = {
        "imdb_rating": "imdb_rating",
        "metascore": "metascore_num",
        "imdb_votes": "imdb_votes_num",
        "title": "title",
        "year": "year",
    }
    sort_col = sort_col_map[sort_by]
    ascending = sort_order == "Ascending"

    # ---- Apply filters ----
    filtered_df = df.copy()

    if search_query:
        filtered_df = filtered_df[
            filtered_df["title"].str.contains(search_query, case=False, na=False)
        ]

    if selected_genres:
        filtered_df = filtered_df[
            filtered_df["genre_list"].apply(lambda x: any(g in selected_genres for g in x))
        ]

    filtered_df = filtered_df[
        (filtered_df["imdb_rating"] >= min_rating) & (filtered_df["imdb_rating"] <= max_rating)
    ]

    if selected_years[0] is not None and "year" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["year"].isna()
            | ((filtered_df["year"] >= selected_years[0]) & (filtered_df["year"] <= selected_years[1]))
        ]

    # ---- Apply sorting ----
    filtered_df = filtered_df.sort_values(by=sort_col, ascending=ascending, na_position="last")

    total_results = len(filtered_df)
    st.subheader(f"Found {total_results} movie(s)")

    if total_results == 0:
        st.info("No movies match your search/filters")
        return

    # ---- Pagination ----
    col_p1, col_p2 = st.columns([1, 3])
    with col_p1:
        page_size = st.selectbox("Movies per page", [10, 20, 50, 100], index=1, key="movies_page_size")

    total_pages = max(1, math.ceil(total_results / page_size))

    # Reset to page 1 if filters changed and current page is out of range
    if "movies_current_page" not in st.session_state:
        st.session_state["movies_current_page"] = 1
    if st.session_state["movies_current_page"] > total_pages:
        st.session_state["movies_current_page"] = 1

    with col_p2:
        current_page = st.number_input(
            f"Page (1 - {total_pages})",
            min_value=1,
            max_value=total_pages,
            value=st.session_state["movies_current_page"],
            step=1,
            key="movies_current_page",
        )

    start_idx = (current_page - 1) * page_size
    end_idx = start_idx + page_size
    page_df = filtered_df.iloc[start_idx:end_idx]

    display_cols = ["title", "imdb_rating", "metascore", "imdb_votes", "year"]
    display_cols = [c for c in display_cols if c in page_df.columns]
    st.dataframe(page_df[display_cols], use_container_width=True, hide_index=True)

    # ---- Pagination controls ----
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    with nav_col1:
        if st.button("⬅️ Previous", disabled=current_page <= 1):
            st.session_state["movies_current_page"] = current_page - 1
            st.rerun()
    with nav_col2:
        st.markdown(
            f"<div style='text-align:center;'>Page {current_page} of {total_pages} "
            f"&nbsp;|&nbsp; Showing {start_idx + 1}-{min(end_idx, total_results)} of {total_results}</div>",
            unsafe_allow_html=True,
        )
    with nav_col3:
        if st.button("Next ➡️", disabled=current_page >= total_pages):
            st.session_state["movies_current_page"] = current_page + 1
            st.rerun()


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
    tab1, tab2 = st.tabs(["Overview", "Movies"])

    with tab1:
        display_overview_tab(df)

    with tab2:
        display_movies_tab(df)




if __name__ == "__main__":
    main()