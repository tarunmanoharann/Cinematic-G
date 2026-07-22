# Cinematic-G - Movie Recommendation System

Production-quality movie discovery and analytics web app using the OMDB API, Knowledge Graphs, and Streamlit.

## Features

- **ETL Pipeline**: Automated data fetching from OMDB API with enrichment and processing
- **Knowledge Graph**: Built with NetworkX using movies, actors, directors, and genres
- **MongoDB Storage**: Persistent storage of all movie data and relationships
- **Content-Based Recommendations**: TF-IDF similarity scoring for movie recommendations
- **Streamlit Dashboard**: Interactive analytics and filtering interface
  - Real-time charts and visualizations
  - Genre, rating, and year filters
  - Movie search functionality
  - Top-rated movies analysis

## Prerequisites

Install these before running the project:

- **Python 3.11 or 3.12** from https://www.python.org/downloads/
- **MongoDB Community Server** from https://www.mongodb.com/try/download/community
- **OMDB API key** from https://www.omdbapi.com/apikey.aspx

## Setup

### 1. Clone and Create Virtual Environment

```bash
cd Cinematic-G
python -m venv venv
```

**Activate on Windows:**
```bash
.\venv\Scripts\activate
```

**Activate on macOS/Linux:**
```bash
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root and fill in your values (you can copy from `.env.example`):

Edit `.env`:
```env
OMDB_API_KEY=your_omdb_api_key_here
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=movies
```

### 4. Ensure MongoDB is Running

**On Windows:**
```bash
mongod
```

**On macOS (with Homebrew):**
```bash
brew services start mongodb-community
```

### 5. Run ETL Pipeline

Fetch and process movie data:

```bash
python -m backend.etl.pipeline
```


This will:
- Fetch movies from OMDB API using common search queries
- Enrich with detailed information (cast, crew, genres, etc.)
- Build knowledge graph relationships
- Store everything in MongoDB
- Train TF-IDF similarity model

### 6. Start Streamlit Dashboard

```bash
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

## Project Structure

```
Cinematic-G/
├── backend/
│   ├── __init__.py
│   ├── config.py              # Configuration settings
│   ├── models.py              # Pydantic data models
│   ├── db/
│   │   ├── __init__.py
│   │   └── mongo.py           # MongoDB operations
│   └── etl/
│       ├── __init__.py
│       ├── omdb_fetcher.py    # OMDB API client
│       ├── processor.py       # Data processing & TF-IDF
│       ├── graph_builder.py   # Knowledge graph construction
│       └── pipeline.py        # ETL orchestration
├── streamlit_app.py           # Main Streamlit dashboard
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── README.md
```


## Technology Stack

- **Backend**: Python
- **Data Processing**: Pandas, NumPy, Scikit-learn
- **Knowledge Graph**: NetworkX
- **Database**: MongoDB with Motor async driver
- **Frontend**: Streamlit with Plotly visualizations
- **API**: Open Movie Database (OMDB) API

## API Configuration

Get your free OMDB API key:
1. Visit https://www.omdbapi.com/apikey.aspx
2. Sign up for a free account
3. Request an API key
4. Copy the API key to your `.env` file

