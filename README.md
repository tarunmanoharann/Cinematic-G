# CineGraph - Movie Recommendation System

Production-quality movie discovery and analytics web app using the TMDb API, Knowledge Graphs, and Streamlit.

## Features

- **ETL Pipeline**: Automated data fetching from TMDb API with enrichment and processing
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
- **TMDb API key** from https://www.themoviedb.org/

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

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:
```env
TMDB_API_KEY=your_tmdb_api_key_here
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

**On Linux:**
```bash
sudo systemctl start mongod
```

### 5. Run ETL Pipeline

Fetch and process movie data (initial run takes 10-30 minutes):

```bash
python -m backend.etl.pipeline
```

This will:
- Fetch popular movies from TMDb API
- Enrich with detailed information (cast, crew, genres)
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
│       ├── tmdb_fetcher.py    # TMDb API client
│       ├── processor.py       # Data processing & TF-IDF
│       ├── graph_builder.py   # Knowledge graph construction
│       └── pipeline.py        # ETL orchestration
├── streamlit_app.py           # Main Streamlit dashboard
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── README.md
```

## Dashboard Features

### Overview Tab
- Total movies count
- Average ratings
- Popularity metrics
- Year range coverage

### Analysis Tab
- Rating distribution histogram
- Popularity trends by year
- Genre distribution (bar chart and pie chart)

### Top Movies Tab
- Customizable top N movies
- Sort by rating, popularity, or vote count

### Filter Tab
- Multi-select genre filtering
- Rating range slider
- Year range slider
- Real-time results

### Search Tab
- Full-text movie title search
- Quick results with overviews

## Technology Stack

- **Backend**: Python, FastAPI
- **Data Processing**: Pandas, NumPy, Scikit-learn
- **Knowledge Graph**: NetworkX
- **Database**: MongoDB with Motor async driver
- **Frontend**: Streamlit with Plotly visualizations
- **API**: The Movie Database (TMDb) v3

## API Configuration

Get your free TMDb API key:
1. Visit https://www.themoviedb.org/settings/api
2. Sign up for an account
3. Request an API key
4. Copy the API key to your `.env` file

## Common Issues

### "ModuleNotFoundError: No module named 'backend'"
Make sure you're running commands from the project root directory:
```bash
# Correct
python -m backend.etl.pipeline

# Wrong
cd backend
python -m etl.pipeline
```

### "MongoDB connection error"
Ensure MongoDB is running:
```bash
# Check if running
mongo --eval "db.adminCommand('ping')"
```

### "requests.exceptions.ConnectionError: No connection"
Check your internet connection and TMDb API key in `.env`

## Performance Notes

- First ETL run: 10-30 minutes (depending on pages fetched)
- Subsequent runs: 5-10 minutes
- Streamlit dashboard: Instant load after data is cached
- MongoDB indexes ensure fast filtering and search

## Future Enhancements

- [ ] Collaborative filtering recommendations
- [ ] User preference profiles
- [ ] Advanced graph traversal algorithms
- [ ] Real-time data updates
- [ ] API endpoint for recommendations
- [ ] Movie watchlist functionality

## License

College Project - 2024

## Support

For issues or questions:
1. Check the README troubleshooting section
2. Verify MongoDB is running
3. Confirm `.env` variables are set correctly
4. Check internet connection for API calls
