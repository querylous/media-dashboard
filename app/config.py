import os
import yaml

_config = None


def load_config():
    global _config
    if _config is not None:
        return _config

    config_path = os.environ.get("CONFIG_PATH", "/config/config.yaml")

    # Fall back to local config.yaml if /config/config.yaml doesn't exist
    if not os.path.exists(config_path):
        local_config = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
        if os.path.exists(local_config):
            config_path = local_config

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            _config = yaml.safe_load(f)
    else:
        # Load from environment variables as fallback
        _config = {
            "tmdb": {
                "api_key": os.environ.get("TMDB_API_KEY", ""),
            },
            "trakt": {
                "client_id": os.environ.get("TRAKT_CLIENT_ID", ""),
            },
            "radarr": {
                "url": os.environ.get("RADARR_URL", "http://localhost:7878"),
                "api_key": os.environ.get("RADARR_API_KEY", ""),
                "root_folder": os.environ.get("RADARR_ROOT_FOLDER", "/movies"),
            },
            "sonarr": {
                "url": os.environ.get("SONARR_URL", "http://localhost:8989"),
                "api_key": os.environ.get("SONARR_API_KEY", ""),
                "root_folder": os.environ.get("SONARR_ROOT_FOLDER", "/tv"),
            },
        }

    return _config


def get_tmdb_config():
    config = load_config()
    return config.get("tmdb", {})


def get_trakt_config():
    config = load_config()
    return config.get("trakt", {})


def get_radarr_config():
    config = load_config()
    return config.get("radarr", {})


def get_sonarr_config():
    config = load_config()
    return config.get("sonarr", {})
