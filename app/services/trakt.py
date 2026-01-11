import requests
from app.config import get_trakt_config

BASE_URL = "https://api.trakt.tv"


def _get_headers():
    config = get_trakt_config()
    return {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": config.get("client_id", ""),
    }


def _make_request(endpoint, params=None):
    headers = _get_headers()
    response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def get_trending_movies(limit=50):
    """Get trending movies on Trakt."""
    data = _make_request("/movies/trending", {"limit": limit, "extended": "full"})
    return _format_movies(data)


def get_popular_movies(limit=50):
    """Get popular movies on Trakt."""
    data = _make_request("/movies/popular", {"limit": limit, "extended": "full"})
    return _format_movies_simple(data)


def get_trending_shows(limit=50):
    """Get trending TV shows on Trakt."""
    data = _make_request("/shows/trending", {"limit": limit, "extended": "full"})
    return _format_shows(data)


def get_popular_shows(limit=50):
    """Get popular TV shows on Trakt."""
    data = _make_request("/shows/popular", {"limit": limit, "extended": "full"})
    return _format_shows_simple(data)


def get_new_movies(limit=50):
    """Get recently released movies."""
    data = _make_request("/calendars/movies/new/today/30", {"limit": limit, "extended": "full"})
    return _format_calendar_movies(data)


def get_new_shows(limit=50):
    """Get new TV show premieres."""
    data = _make_request("/calendars/shows/new/today/30", {"limit": limit, "extended": "full"})
    return _format_calendar_shows(data)


def _format_movies(results):
    """Format trending movie results."""
    movies = []
    for item in results:
        movie = item.get("movie", {})
        movies.append({
            "trakt_id": movie.get("ids", {}).get("trakt"),
            "tmdb_id": movie.get("ids", {}).get("tmdb"),
            "imdb_id": movie.get("ids", {}).get("imdb"),
            "title": movie.get("title", "Unknown"),
            "year": movie.get("year"),
            "overview": movie.get("overview", ""),
            "rating": round(movie.get("rating", 0), 1),
            "release_date": movie.get("released"),
            "media_type": "movie",
            "watchers": item.get("watchers", 0),
        })
    return movies


def _format_movies_simple(results):
    """Format popular movie results (different structure)."""
    movies = []
    for movie in results:
        movies.append({
            "trakt_id": movie.get("ids", {}).get("trakt"),
            "tmdb_id": movie.get("ids", {}).get("tmdb"),
            "imdb_id": movie.get("ids", {}).get("imdb"),
            "title": movie.get("title", "Unknown"),
            "year": movie.get("year"),
            "overview": movie.get("overview", ""),
            "rating": round(movie.get("rating", 0), 1),
            "release_date": movie.get("released"),
            "media_type": "movie",
        })
    return movies


def _format_shows(results):
    """Format trending TV show results."""
    shows = []
    for item in results:
        show = item.get("show", {})
        shows.append({
            "trakt_id": show.get("ids", {}).get("trakt"),
            "tmdb_id": show.get("ids", {}).get("tmdb"),
            "tvdb_id": show.get("ids", {}).get("tvdb"),
            "imdb_id": show.get("ids", {}).get("imdb"),
            "title": show.get("title", "Unknown"),
            "year": show.get("year"),
            "overview": show.get("overview", ""),
            "rating": round(show.get("rating", 0), 1),
            "first_air_date": show.get("first_aired"),
            "media_type": "tv",
            "watchers": item.get("watchers", 0),
        })
    return shows


def _format_shows_simple(results):
    """Format popular TV show results (different structure)."""
    shows = []
    for show in results:
        shows.append({
            "trakt_id": show.get("ids", {}).get("trakt"),
            "tmdb_id": show.get("ids", {}).get("tmdb"),
            "tvdb_id": show.get("ids", {}).get("tvdb"),
            "imdb_id": show.get("ids", {}).get("imdb"),
            "title": show.get("title", "Unknown"),
            "year": show.get("year"),
            "overview": show.get("overview", ""),
            "rating": round(show.get("rating", 0), 1),
            "first_air_date": show.get("first_aired"),
            "media_type": "tv",
        })
    return shows


def _format_calendar_movies(results):
    """Format calendar movie results."""
    movies = []
    for item in results:
        movie = item.get("movie", {})
        movies.append({
            "trakt_id": movie.get("ids", {}).get("trakt"),
            "tmdb_id": movie.get("ids", {}).get("tmdb"),
            "imdb_id": movie.get("ids", {}).get("imdb"),
            "title": movie.get("title", "Unknown"),
            "year": movie.get("year"),
            "overview": movie.get("overview", ""),
            "rating": round(movie.get("rating", 0), 1),
            "release_date": item.get("released"),
            "media_type": "movie",
        })
    return movies


def _format_calendar_shows(results):
    """Format calendar show results."""
    shows = []
    seen_ids = set()
    for item in results:
        show = item.get("show", {})
        tmdb_id = show.get("ids", {}).get("tmdb")
        if tmdb_id in seen_ids:
            continue
        seen_ids.add(tmdb_id)
        shows.append({
            "trakt_id": show.get("ids", {}).get("trakt"),
            "tmdb_id": tmdb_id,
            "tvdb_id": show.get("ids", {}).get("tvdb"),
            "imdb_id": show.get("ids", {}).get("imdb"),
            "title": show.get("title", "Unknown"),
            "year": show.get("year"),
            "overview": show.get("overview", ""),
            "rating": round(show.get("rating", 0), 1),
            "first_air_date": item.get("first_aired"),
            "media_type": "tv",
        })
    return shows
