import requests
from app.config import get_tmdb_config

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


def _get_headers():
    config = get_tmdb_config()
    return {
        "Authorization": f"Bearer {config.get('api_key', '')}",
        "Content-Type": "application/json",
    }


def _make_request(endpoint, params=None):
    config = get_tmdb_config()
    api_key = config.get("api_key", "")

    if params is None:
        params = {}
    params["api_key"] = api_key

    response = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def get_trending_movies(page=1):
    """Get trending movies for the week."""
    data = _make_request("/trending/movie/week", {"page": page})
    return _format_movies(data.get("results", []))


def get_trending_shows(page=1):
    """Get trending TV shows for the week."""
    data = _make_request("/trending/tv/week", {"page": page})
    return _format_shows(data.get("results", []))


def search_movies(query, page=1):
    """Search for movies by title."""
    data = _make_request("/search/movie", {"query": query, "page": page})
    return _format_movies(data.get("results", []))


def search_shows(query, page=1):
    """Search for TV shows by title."""
    data = _make_request("/search/tv", {"query": query, "page": page})
    return _format_shows(data.get("results", []))


def get_movie_details(tmdb_id):
    """Get detailed info for a movie."""
    data = _make_request(f"/movie/{tmdb_id}", {"append_to_response": "external_ids"})
    return data


def get_show_details(tmdb_id):
    """Get detailed info for a TV show."""
    data = _make_request(f"/tv/{tmdb_id}", {"append_to_response": "external_ids"})
    return data


def _format_movies(results):
    """Format movie results into a consistent structure."""
    movies = []
    for item in results:
        movies.append({
            "tmdb_id": item.get("id"),
            "title": item.get("title", "Unknown"),
            "year": item.get("release_date", "")[:4] if item.get("release_date") else None,
            "overview": item.get("overview", ""),
            "poster": f"{IMAGE_BASE_URL}{item.get('poster_path')}" if item.get("poster_path") else None,
            "rating": round(item.get("vote_average", 0), 1),
            "release_date": item.get("release_date"),
            "media_type": "movie",
        })
    return movies


def _format_shows(results):
    """Format TV show results into a consistent structure."""
    shows = []
    for item in results:
        shows.append({
            "tmdb_id": item.get("id"),
            "title": item.get("name", "Unknown"),
            "year": item.get("first_air_date", "")[:4] if item.get("first_air_date") else None,
            "overview": item.get("overview", ""),
            "poster": f"{IMAGE_BASE_URL}{item.get('poster_path')}" if item.get("poster_path") else None,
            "rating": round(item.get("vote_average", 0), 1),
            "first_air_date": item.get("first_air_date"),
            "media_type": "tv",
        })
    return shows
