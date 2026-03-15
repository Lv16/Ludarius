import hashlib
import logging

import requests
from django.conf import settings
from django.core.cache import cache

BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE = "/tmdb/image/w500"
TMDB_TIMEOUT = 8

logger = logging.getLogger(__name__)


def _img(path: str | None) -> str:
    if not path:
        return ""
    return f"{IMG_BASE}/{path.lstrip('/')}"


def _tmdb_get(endpoint: str, *, params: dict | None = None, cache_key: str | None = None, ttl: int | None = None) -> dict:
    if cache_key:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    api_key = settings.TMDB_API_KEY
    if not api_key:
        raise RuntimeError("TMDB_API_KEY is not configured")

    query = {"api_key": api_key, **(params or {})}
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"

    try:
        response = requests.get(url, params=query, timeout=TMDB_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        logger.exception("TMDB request failed", extra={"endpoint": endpoint, "params": params or {}})
        raise

    if cache_key and ttl:
        cache.set(cache_key, payload, ttl)
    return payload


def search_multi(query: str, page: int = 1) -> dict:
    q = (query or "").strip().lower()
    if not q:
        return {"results": [], "page": 1, "total_pages": 1}

    qhash = hashlib.md5(q.encode("utf-8")).hexdigest()
    data = _tmdb_get(
        "search/multi",
        params={
            "query": query,
            "language": "pt-BR",
            "page": page,
            "include_adult": "false",
        },
        cache_key=f"tmdb:search:multi:ptbr:p{page}:{qhash}",
        ttl=60 * 3,
    )

    results = []
    for item in data.get("results", []):
        media_type = item.get("media_type")
        if media_type not in ("movie", "tv"):
            continue

        if media_type == "movie":
            results.append(
                {
                    "media_type": "movie",
                    "tmdb_id": item.get("id"),
                    "title": item.get("title") or "",
                    "date": item.get("release_date") or "",
                    "rating": item.get("vote_average"),
                    "poster_url": _img(item.get("poster_path")),
                }
            )
        else:
            results.append(
                {
                    "media_type": "tv",
                    "tmdb_id": item.get("id"),
                    "title": item.get("name") or "",
                    "date": item.get("first_air_date") or "",
                    "rating": item.get("vote_average"),
                    "poster_url": _img(item.get("poster_path")),
                }
            )

    return {
        "results": results,
        "page": data.get("page", page),
        "total_pages": data.get("total_pages", 1),
    }


def search_movies(query, page=1):
    data = _tmdb_get(
        "search/movie",
        params={
            "query": query,
            "language": "pt-BR",
            "page": page,
            "include_adult": False,
        },
    )

    results = []
    for item in data.get("results", []):
        results.append(
            {
                "tmdb_id": item.get("id"),
                "title": item.get("title") or "",
                "original_title": item.get("original_title") or "",
                "release_date": item.get("release_date") or "",
                "rating": item.get("vote_average"),
                "poster_url": _img(item.get("poster_path")),
            }
        )
    return results


def get_movie_details(tmdb_id: int) -> dict:
    data = _tmdb_get(
        f"movie/{tmdb_id}",
        params={"language": "pt-BR"},
        cache_key=f"tmdb:detail:movie:{tmdb_id}:ptbr",
        ttl=60 * 30,
    )
    return {
        "tmdb_id": data.get("id"),
        "title": data.get("title") or "",
        "original_title": data.get("original_title") or "",
        "overview": data.get("overview") or "",
        "release_date": data.get("release_date") or "",
        "rating": data.get("vote_average"),
        "poster_url": _img(data.get("poster_path")),
        "backdrop_url": _img(data.get("backdrop_path")),
        "genres": [genre.get("name") for genre in data.get("genres", []) if genre.get("name")],
        "runtime": data.get("runtime"),
    }


def get_movie_watch_providers(tmdb_id: int, region: str = "BR") -> dict:
    data = _tmdb_get(
        f"movie/{tmdb_id}/watch/providers",
        cache_key=f"tmdb:watch:movie:{tmdb_id}",
        ttl=60 * 30,
    )
    results = data.get("results", {}) or {}
    region_data = results.get(region, {}) or {}

    def _map_list(key: str) -> list[dict]:
        return [
            {"name": provider.get("provider_name"), "logo_url": _img(provider.get("logo_path"))}
            for provider in (region_data.get(key, []) or [])
        ]

    return {
        "link": region_data.get("link") or "",
        "flatrate": _map_list("flatrate"),
        "rent": _map_list("rent"),
        "buy": _map_list("buy"),
    }


def search_tv(query: str, page: int = 1) -> list[dict]:
    data = _tmdb_get(
        "search/tv",
        params={
            "query": query,
            "language": "pt-BR",
            "page": page,
            "include_adult": False,
        },
    )
    results = []
    for item in data.get("results", []):
        results.append(
            {
                "tmdb_id": item.get("id"),
                "name": item.get("name") or "",
                "original_name": item.get("original_name") or "",
                "first_air_date": item.get("first_air_date") or "",
                "rating": item.get("vote_average"),
                "poster_url": _img(item.get("poster_path")),
            }
        )
    return results


def get_tv_details(tmdb_id: int) -> dict:
    data = _tmdb_get(
        f"tv/{tmdb_id}",
        params={"language": "pt-BR"},
        cache_key=f"tmdb:detail:tv:{tmdb_id}:ptbr",
        ttl=60 * 30,
    )
    return {
        "tmdb_id": data.get("id"),
        "name": data.get("name") or "",
        "original_name": data.get("original_name") or "",
        "overview": data.get("overview") or "",
        "first_air_date": data.get("first_air_date") or "",
        "last_air_date": data.get("last_air_date") or "",
        "rating": data.get("vote_average"),
        "poster_url": _img(data.get("poster_path")),
        "backdrop_url": _img(data.get("backdrop_path")),
        "genres": [genre.get("name") for genre in data.get("genres", []) if genre.get("name")],
        "number_of_seasons": data.get("number_of_seasons"),
        "number_of_episodes": data.get("number_of_episodes"),
        "status": data.get("status") or "",
    }


def get_tv_watch_providers(tmdb_id: int, region: str = "BR") -> dict:
    data = _tmdb_get(
        f"tv/{tmdb_id}/watch/providers",
        cache_key=f"tmdb:watch:tv:{tmdb_id}",
        ttl=60 * 30,
    )
    results = data.get("results", {}) or {}
    country = results.get(region, {}) or {}

    def _map_list(key: str) -> list[dict]:
        return [
            {"name": provider.get("provider_name") or "", "logo_url": _img(provider.get("logo_path"))}
            for provider in (country.get(key, []) or [])
        ]

    return {
        "link": country.get("link") or "",
        "flatrate": _map_list("flatrate"),
        "rent": _map_list("rent"),
        "buy": _map_list("buy"),
    }


def get_trending_tv() -> list[dict]:
    data = _tmdb_get(
        "trending/tv/day",
        params={"language": "pt-BR"},
        cache_key="tmdb:trending:tv:day:ptbr",
        ttl=60 * 10,
    )

    results = []
    for item in data.get("results", []):
        results.append(
            {
                "tmdb_id": item.get("id"),
                "name": item.get("name") or "",
                "first_air_date": item.get("first_air_date") or "",
                "rating": item.get("vote_average"),
                "poster_url": _img(item.get("poster_path")),
            }
        )
    return results


def get_trending_movies(region: str = "BR", language: str = "pt-BR") -> list[dict]:
    data = _tmdb_get(
        "trending/movie/day",
        params={"language": language},
        cache_key=f"tmdb:trending:movie:day:{language.lower()}:{region.lower()}",
        ttl=60 * 10,
    )

    results = []
    for item in data.get("results", []):
        results.append(
            {
                "tmdb_id": item.get("id"),
                "title": item.get("title") or "",
                "release_date": item.get("release_date") or "",
                "rating": item.get("vote_average"),
                "poster_url": _img(item.get("poster_path")),
            }
        )
    return results


def get_popular_movies() -> list[dict]:
    data = _tmdb_get(
        "movie/popular",
        params={"language": "pt-BR", "page": 1},
        cache_key="tmdb:popular:movie:ptbr",
        ttl=60 * 30,
    )

    results = []
    for item in data.get("results", []):
        results.append(
            {
                "tmdb_id": item.get("id"),
                "title": item.get("title") or "",
                "release_date": item.get("release_date") or "",
                "rating": item.get("vote_average"),
                "poster_url": _img(item.get("poster_path")),
            }
        )
    return results


def get_popular_tv() -> list[dict]:
    data = _tmdb_get(
        "tv/popular",
        params={"language": "pt-BR", "page": 1},
        cache_key="tmdb:popular:tv:ptbr",
        ttl=60 * 30,
    )

    results = []
    for item in data.get("results", []):
        results.append(
            {
                "tmdb_id": item.get("id"),
                "name": item.get("name") or "",
                "first_air_date": item.get("first_air_date") or "",
                "rating": item.get("vote_average"),
                "poster_url": _img(item.get("poster_path")),
            }
        )
    return results


def get_top_rated_movies() -> list[dict]:
    data = _tmdb_get(
        "movie/top_rated",
        params={"language": "pt-BR", "page": 1},
        cache_key="tmdb:toprated:movie:ptbr",
        ttl=60 * 30,
    )

    results = []
    for item in data.get("results", []):
        results.append(
            {
                "tmdb_id": item.get("id"),
                "title": item.get("title") or "",
                "release_date": item.get("release_date") or "",
                "rating": item.get("vote_average"),
                "poster_url": _img(item.get("poster_path")),
            }
        )
    return results


def get_top_rated_tv() -> list[dict]:
    data = _tmdb_get(
        "tv/top_rated",
        params={"language": "pt-BR", "page": 1},
        cache_key="tmdb:toprated:tv:ptbr",
        ttl=60 * 30,
    )

    results = []
    for item in data.get("results", []):
        results.append(
            {
                "tmdb_id": item.get("id"),
                "name": item.get("name") or "",
                "first_air_date": item.get("first_air_date") or "",
                "rating": item.get("vote_average"),
                "poster_url": _img(item.get("poster_path")),
            }
        )
    return results
