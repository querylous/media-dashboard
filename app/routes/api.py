from flask import Blueprint, jsonify, request
from app.services import tmdb, trakt, radarr, sonarr
from app.config import get_plex_config

api = Blueprint("api", __name__, url_prefix="/api")


def merge_movies(tmdb_movies, trakt_movies, limit=50):
    """Merge and deduplicate movies from TMDB and Trakt."""
    seen_ids = set()
    merged = []

    # Add TMDB movies first (better poster data)
    for movie in tmdb_movies:
        tmdb_id = movie.get("tmdb_id")
        if tmdb_id and tmdb_id not in seen_ids:
            seen_ids.add(tmdb_id)
            merged.append(movie)

    # Add Trakt movies that aren't already in the list
    for movie in trakt_movies:
        tmdb_id = movie.get("tmdb_id")
        if tmdb_id and tmdb_id not in seen_ids:
            seen_ids.add(tmdb_id)
            merged.append(movie)

    return merged[:limit]


def merge_shows(tmdb_shows, trakt_shows, limit=50):
    """Merge and deduplicate shows from TMDB and Trakt."""
    seen_ids = set()
    merged = []

    # Add TMDB shows first (better poster data)
    for show in tmdb_shows:
        tmdb_id = show.get("tmdb_id")
        if tmdb_id and tmdb_id not in seen_ids:
            seen_ids.add(tmdb_id)
            merged.append(show)

    # Add Trakt shows that aren't already in the list
    for show in trakt_shows:
        tmdb_id = show.get("tmdb_id")
        if tmdb_id and tmdb_id not in seen_ids:
            seen_ids.add(tmdb_id)
            merged.append(show)

    return merged[:limit]


@api.route("/movies")
def get_movies():
    """Get top 50 trending/new movies."""
    try:
        # Get from both sources
        tmdb_movies = tmdb.get_trending_movies(page=1)
        tmdb_movies_p2 = tmdb.get_trending_movies(page=2)
        trakt_movies = trakt.get_trending_movies(limit=50)

        # Merge and deduplicate
        merged = merge_movies(tmdb_movies + tmdb_movies_p2, trakt_movies, limit=50)

        return jsonify({"success": True, "data": merged})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/shows")
def get_shows():
    """Get top 50 trending/new TV shows."""
    try:
        # Get from both sources
        tmdb_shows = tmdb.get_trending_shows(page=1)
        tmdb_shows_p2 = tmdb.get_trending_shows(page=2)
        trakt_shows = trakt.get_trending_shows(limit=50)

        # Merge and deduplicate
        merged = merge_shows(tmdb_shows + tmdb_shows_p2, trakt_shows, limit=50)

        return jsonify({"success": True, "data": merged})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/search/movies")
def search_movies():
    """Search for movies by title."""
    query = request.args.get("query", "")
    if not query:
        return jsonify({"success": False, "error": "Query parameter required"}), 400

    try:
        results = tmdb.search_movies(query)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/search/shows")
def search_shows():
    """Search for TV shows by title."""
    query = request.args.get("query", "")
    if not query:
        return jsonify({"success": False, "error": "Query parameter required"}), 400

    try:
        results = tmdb.search_shows(query)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/radarr/library")
def get_radarr_library():
    """Get TMDB IDs of movies in Radarr."""
    try:
        tmdb_ids = list(radarr.get_library_tmdb_ids())
        return jsonify({"success": True, "data": tmdb_ids})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/sonarr/library")
def get_sonarr_library():
    """Get TVDB IDs of shows in Sonarr."""
    try:
        tvdb_ids = list(sonarr.get_library_tvdb_ids())
        return jsonify({"success": True, "data": tvdb_ids})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/radarr/profiles")
def get_radarr_profiles():
    """Get Radarr quality profiles."""
    try:
        profiles = radarr.get_quality_profiles()
        return jsonify({"success": True, "data": profiles})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/sonarr/profiles")
def get_sonarr_profiles():
    """Get Sonarr quality profiles."""
    try:
        profiles = sonarr.get_quality_profiles()
        return jsonify({"success": True, "data": profiles})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/radarr/add", methods=["POST"])
def add_to_radarr():
    """Add a movie to Radarr."""
    data = request.get_json()
    tmdb_id = data.get("tmdb_id")
    quality_profile_id = data.get("quality_profile_id")

    if not tmdb_id:
        return jsonify({"success": False, "error": "tmdb_id required"}), 400
    if not quality_profile_id:
        return jsonify({"success": False, "error": "quality_profile_id required"}), 400

    try:
        result = radarr.add_movie(tmdb_id, quality_profile_id)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/sonarr/add", methods=["POST"])
def add_to_sonarr():
    """Add a TV show to Sonarr."""
    data = request.get_json()
    tvdb_id = data.get("tvdb_id")
    tmdb_id = data.get("tmdb_id")
    quality_profile_id = data.get("quality_profile_id")

    if not tvdb_id and not tmdb_id:
        return jsonify({"success": False, "error": "tvdb_id or tmdb_id required"}), 400
    if not quality_profile_id:
        return jsonify({"success": False, "error": "quality_profile_id required"}), 400

    try:
        result = sonarr.add_series(
            tvdb_id=tvdb_id,
            tmdb_id=tmdb_id,
            quality_profile_id=quality_profile_id
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/status")
def get_status():
    """Check connection status to Radarr and Sonarr."""
    radarr_status = radarr.test_connection()
    sonarr_status = sonarr.test_connection()

    return jsonify({
        "success": True,
        "radarr": radarr_status,
        "sonarr": sonarr_status,
    })


@api.route("/plex/config")
def get_plex_url():
    """Get Plex URL for watch links."""
    config = get_plex_config()
    return jsonify({
        "success": True,
        "url": config.get("url", "https://app.plex.tv/desktop"),
    })
