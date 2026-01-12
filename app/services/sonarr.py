import requests
from app.config import get_sonarr_config


def _get_base_url():
    config = get_sonarr_config()
    return config.get("url", "http://localhost:8989").rstrip("/")


def _get_headers():
    config = get_sonarr_config()
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
    """Get all series in Sonarr library."""
    series = _make_request("/series")
    return {s.get("tvdbId"): s for s in series}


def get_library_tvdb_ids():
    """Get set of TVDB IDs for series in library."""
    series = _make_request("/series")
    return {s.get("tvdbId") for s in series if s.get("tvdbId")}


def get_library_tmdb_ids():
    """Get set of TMDB IDs for series in library."""
    series = _make_request("/series")
    return {s.get("tmdbId") for s in series if s.get("tmdbId")}


def get_library_with_status():
    """Get library with download status."""
    series_list = _make_request("/series")
    queue = _make_request("/queue")

    # Get series IDs and progress currently downloading
    downloading_progress = {}
    for item in queue.get("records", []):
        series_id = item.get("seriesId")
        if series_id:
            size = item.get("size", 0)
            sizeleft = item.get("sizeleft", 0)
            if size > 0:
                progress = round((1 - sizeleft / size) * 100)
            else:
                progress = 0
            # Keep the highest progress if multiple episodes downloading
            if series_id not in downloading_progress or progress > downloading_progress[series_id]:
                downloading_progress[series_id] = progress

    result = {
        "downloaded": {"tvdb": [], "tmdb": []},
        "downloading": {"tvdb": {}, "tmdb": {}},
        "missing": {"tvdb": [], "tmdb": []}
    }

    for series in series_list:
        tvdb_id = series.get("tvdbId")
        tmdb_id = series.get("tmdbId")
        series_id = series.get("id")
        stats = series.get("statistics", {})
        episode_file_count = stats.get("episodeFileCount", 0)

        if series_id in downloading_progress:
            progress = downloading_progress[series_id]
            if tvdb_id:
                result["downloading"]["tvdb"][tvdb_id] = progress
            if tmdb_id:
                result["downloading"]["tmdb"][tmdb_id] = progress
        elif episode_file_count > 0:
            if tvdb_id:
                result["downloaded"]["tvdb"].append(tvdb_id)
            if tmdb_id:
                result["downloaded"]["tmdb"].append(tmdb_id)
        else:
            if tvdb_id:
                result["missing"]["tvdb"].append(tvdb_id)
            if tmdb_id:
                result["missing"]["tmdb"].append(tmdb_id)

    return result


def get_quality_profiles():
    """Get available quality profiles."""
    profiles = _make_request("/qualityprofile")
    return [{"id": p.get("id"), "name": p.get("name")} for p in profiles]


def get_root_folders():
    """Get available root folders."""
    folders = _make_request("/rootfolder")
    return [{"id": f.get("id"), "path": f.get("path")} for f in folders]


def lookup_series(tvdb_id):
    """Lookup series details by TVDB ID."""
    results = _make_request(f"/series/lookup?term=tvdb:{tvdb_id}")
    return results[0] if results else None


def lookup_series_by_tmdb(tmdb_id):
    """Lookup series details by TMDB ID."""
    results = _make_request(f"/series/lookup?term=tmdb:{tmdb_id}")
    return results[0] if results else None


def add_series(tvdb_id=None, tmdb_id=None, quality_profile_id=None, root_folder_path=None):
    """Add a series to Sonarr."""
    config = get_sonarr_config()

    # Lookup series first
    if tvdb_id:
        series = lookup_series(tvdb_id)
    elif tmdb_id:
        series = lookup_series_by_tmdb(tmdb_id)
    else:
        raise ValueError("Either tvdb_id or tmdb_id is required")

    if not series:
        raise ValueError(f"Series not found")

    # Use provided root folder or default from config
    if not root_folder_path:
        root_folder_path = config.get("root_folder", "/tv")

    # Prepare series data
    series_data = {
        "tvdbId": series.get("tvdbId"),
        "title": series.get("title"),
        "year": series.get("year"),
        "qualityProfileId": quality_profile_id,
        "rootFolderPath": root_folder_path,
        "monitored": True,
        "seasonFolder": True,
        "addOptions": {
            "searchForMissingEpisodes": True,
        },
    }

    return _make_request("/series", method="POST", data=series_data)


def test_connection():
    """Test connection to Sonarr."""
    try:
        _make_request("/system/status")
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
