# CineGraph - Movie Recommendation System

Production-quality movie discovery and recommendation web app using the TMDb API and Knowledge Graphs.

## Features

- **Heterogeneous Knowledge Graph**: Built with NetworkX using movies, actors, directors, and genres.
- **Hybrid Recommendation Engine**: Combines TF-IDF content similarity with knowledge graph multi-hop traversal.
- **MongoDB Backend**: Stores user profiles and interactions in MongoDB.

## Prerequisites

Install these before running the project:

- **Python 3.11 or 3.12** from <https://www.python.org/downloads/>
- **Node.js 20+** from <https://nodejs.org/>
- **MongoDB Community Server** from <https://www.mongodb.com/try/download/community>
- **TMDb API key** from <https://www.themoviedb.org/>

During Python installation on Windows, tick **Add python.exe to PATH**.

## Backend Setup With Virtual Environment

Run these commands from the project root folder.

### 1. Create the Virtual Environment

```powershell
cd backend
py -3.11 -m venv .venv
```

If `py -3.11` does not work, try:

```powershell
python -m venv .venv
```

### 2. Activate the Virtual Environment

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Command Prompt:

```cmd
.\.venv\Scripts\activate.bat
```

Git Bash:

```bash
source .venv/Scripts/activate
```

After activation, your terminal should show `(.venv)` at the start of the prompt.

If PowerShell blocks activation, run this once:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Backend Dependencies

Make sure the virtual environment is active first.

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

Open `backend/.env` and set:

```env
TMDB_API_KEY=your_tmdb_api_key_here
SECRET_KEY=use_a_long_random_secret_here
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=movies
```

Make sure MongoDB is running before starting the backend.

### 5. Run the Data Pipeline

From the project root folder, with the backend virtual environment active:

```powershell
cd ..
python -m backend.etl.pipeline
```

The first run can take 30-60 minutes because it fetches movie data, builds the knowledge graph, and trains the TF-IDF model.

### 6. Start the Backend Server

From the project root folder, with the backend virtual environment active:

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

Backend URL:

```text
http://localhost:8000
```

## Visual Studio / VS Code Setup

If your friend is getting dependency errors, they are probably using the wrong Python interpreter.

### VS Code

1. Open the project folder in VS Code.
2. Press `Ctrl + Shift + P`.
3. Search for `Python: Select Interpreter`.
4. Choose:

```text
backend\.venv\Scripts\python.exe
```

5. Open a new terminal and confirm:

```powershell
python -c "import sys; print(sys.executable)"
```

It should print a path inside `backend\.venv`.

### Visual Studio

1. Open the project in Visual Studio.
2. Go to **View > Other Windows > Python Environments**.
3. Add or select the virtual environment at:

```text
backend\.venv
```

4. Make sure packages are installed using that environment, not global Python.

## Frontend Setup

Open a second terminal from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

## Common Dependency Fixes

### `python` or `py` is not recognized

Install Python again and tick **Add python.exe to PATH**. Then close and reopen Visual Studio, VS Code, and the terminal.

### Packages install but imports still fail

You are probably not inside the virtual environment. Run:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Then select `backend\.venv\Scripts\python.exe` as the interpreter.

### `pip` installs to the wrong Python

Use this instead of plain `pip`:

```powershell
python -m pip install -r requirements.txt
```

### `uvicorn` is not recognized

Run uvicorn through Python:

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

### `ModuleNotFoundError: No module named backend`

Run backend commands from the project root folder, not from inside `backend`.

Correct:

```powershell
cd C:\path\to\4628
python -m uvicorn backend.main:app --reload --port 8000
```

Incorrect:

```powershell
cd backend
python -m uvicorn backend.main:app --reload --port 8000
```

### MongoDB connection error

Start MongoDB locally and check that `.env` contains:

```env
MONGODB_URL=mongodb://localhost:27017
```

## Tech Stack

- **Frontend**: React, TailwindCSS, Zustand, React Router, Axios.
- **Backend**: FastAPI, MongoDB, NetworkX, Scikit-learn, Pandas.
- **Data**: TMDb API.
