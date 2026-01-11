import requests
from app.config import get_radarr_config


def _get_base_url():
    config = get_radarr_config()
    return config.get("url", "http://localhost:7878").rstrip("/")


def _get_headers():
    config = get_radarr_config()
    return {
        "X-Api-Key": config.get("api_key", ""),
        "Content-Type": "application/json",
    }


def _make_request(endpoint, method="GET", data=None):
    url = f"{_get_base_url()}/api/v3{endpoint}"
    headers = _get_headers()

    if method == "GET":
        response = requests.get(url, headers=headers, timeout=10)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data, timeout=10)
    else:
        raise ValueError(f"Unsupported method: {method}")

    response.raise_for_status()
    return response.json() if response.text else None


def get_library():
    """Get all movies in Radarr library."""
    movies = _make_request("/movie")
    return {movie.get("tmdbId"): movie for movie in movies}


def get_library_tmdb_ids():
    """Get set of TMDB IDs for movies in library."""
    movies = _make_request("/movie")
    return {movie.get("tmdbId") for movie in movies if movie.get("tmdbId")}


def get_quality_profiles():
    """Get available quality profiles."""
    profiles = _make_request("/qualityprofile")
    return [{"id": p.get("id"), "name": p.get("name")} for p in profiles]


def get_root_folders():
    """Get available root folders."""
    folders = _make_request("/rootfolder")
    return [{"id": f.get("id"), "path": f.get("path")} for f in folders]


def lookup_movie(tmdb_id):
    """Lookup movie details by TMDB ID."""
    results = _make_request(f"/movie/lookup/tmdb?tmdbId={tmdb_id}")
    return results


def add_movie(tmdb_id, quality_profile_id, root_folder_path=None):
    """Add a movie to Radarr."""
    config = get_radarr_config()

    # Lookup movie first
    movie = lookup_movie(tmdb_id)
    if not movie:
        raise ValueError(f"Movie with TMDB ID {tmdb_id} not found")

    # Use provided root folder or default from config
    if not root_folder_path:
        root_folder_path = config.get("root_folder", "/movies")

    # Prepare movie data
    movie_data = {
        "tmdbId": movie.get("tmdbId"),
        "title": movie.get("title"),
        "year": movie.get("year"),
        "qualityProfileId": quality_profile_id,
        "rootFolderPath": root_folder_path,
        "monitored": True,
        "addOptions": {
            "searchForMovie": True,
        },
    }

    return _make_request("/movie", method="POST", data=movie_data)


def test_connection():
    """Test connection to Radarr."""
    try:
        _make_request("/system/status")
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
