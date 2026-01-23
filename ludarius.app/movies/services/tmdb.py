import requests 
from django.conf import settings

BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/w500"

def _img(path: str | None) -> str:
    if not path:
        return ""
    return f"{IMG_BASE}{path}"

def search_multi(query: str, page: int = 1) -> list[dict]:
    url = f"{BASE_URL}/search/multi"
    params = {
        "api_key": settings.TMDB_API_KEY,
        "query": query,
        "language": "pt-BR",
        "page": page,
        "include_adult": "false",
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()

    results = []
    for r in data.get("results", []):
        media_type = r.get("media_type")
        if media_type not in ("movie", "tv"):
            continue  # ignora pessoas etc.

        if media_type == "movie":
            results.append({
                "media_type": "movie",
                "tmdb_id": r.get("id"),
                "title": r.get("title") or "",
                "date": r.get("release_date") or "",
                "rating": r.get("vote_average"),
                "poster_url": _img(r.get("poster_path")),
            })
        else:
            results.append({
                "media_type": "tv",
                "tmdb_id": r.get("id"),
                "title": r.get("name") or "",
                "date": r.get("first_air_date") or "",
                "rating": r.get("vote_average"),
                "poster_url": _img(r.get("poster_path")),
            })

    return results


def search_movies(query, page=1):
    url = f"{BASE_URL}/search/movie"
    params = {
        "api_key": settings.TMDB_API_KEY,
        "query": query,
        "language": "pt-BR",
        "page": page,
        "include_adult": False,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    results = []
    for r in data.get("results", []):
        results.append({
            "tmdb_id": r.get("id"),
            "title": r.get("title") or "",
            "original_title": r.get("original_title") or "",
            "release_date": r.get("release_date") or "",
            "rating": r.get("vote_average"),
            "poster_url": _img(r.get("poster_path")),
        })
        
    return results

def get_movie_details(tmdb_id: int) -> dict:
    url = f"{BASE_URL}/movie/{tmdb_id}"
    params = {
        "api_key": settings.TMDB_API_KEY,
        "language": "pt-BR",
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    r = res.json()
    
    return {
        "tmdb_id": r.get("id"),
        "title": r.get("title") or "",
        "original_title": r.get("original_title") or "",
        "overview": r.get("overview") or "",
        "release_date": r.get("release_date") or "",
        "rating": r.get("vote_average"),
        "poster_url": _img(r.get("poster_path")),
        "backdrop_url": _img(r.get("backdrop_path")),
        "genres": [g.get("name") for g in r.get("genres", []) if g.get("name")],
        "runtime": r.get("runtime"),
    }

def get_movie_watch_providers(tmdb_id: int, region: str = "BR") -> dict:
    url = f"{BASE_URL}/movie/{tmdb_id}/watch/providers"
    params = {"api_key": settings.TMDB_API_KEY}
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()
    
    results = data.get("results", {}) or {}
    region_data = results.get(region, {}) or {}

    def _map_list(key: str) -> list[dict]:
        items = region_data.get(key, []) or []
        mapped = []
        for p in items:
            mapped.append({
                "name": p.get("provider_name"),
                "logo_url": _img(p.get("logo_path")),
            })
        return mapped

    return {
        "link": region_data.get("link") or "",
        "flatrate": _map_list("flatrate"),
        "rent": _map_list("rent"),
        "buy": _map_list("buy"),
    }
    
def search_tv(query: str, page: int = 1) -> list[dict]:
    url = f"{BASE_URL}/search/tv"
    params = {
        "api_key": settings.TMDB_API_KEY,
        "query": query,
        "language": "pt-BR",
        "page": page,
        "include_adult": False,
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()
    results = []
    for r in data.get("results", []):
        results.append({
            "tmdb_id": r.get("id"),
            "name": r.get("name") or "",
            "original_name": r.get("original_name") or "",
            "first_air_date": r.get("first_air_date") or "",
            "rating": r.get("vote_average"),
            "poster_url": _img(r.get("poster_path")),
        })
    return results
    
def get_tv_details(tmdb_id: int) -> dict:
    url = f"{BASE_URL}/tv/{tmdb_id}"
    params = {
        "api_key": settings.TMDB_API_KEY,
        "language": "pt-BR",
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    r = res.json()
    
    return {
        "tmdb_id": r.get("id"),
        "name": r.get("name") or "",
        "original_name": r.get("original_name") or "",
        "overview": r.get("overview") or "",
        "first_air_date": r.get("first_air_date") or "",
        "last_air_date": r.get("last_air_date") or "",
        "rating": r.get("vote_average"),
        "poster_url": _img(r.get("poster_path")),
        "backdrop_url": _img(r.get("backdrop_path")),
        "genres": [g.get("name") for g in r.get("genres", []) if g.get("name")],
        "number_of_seasons": r.get("number_of_seasons"),
        "number_of_episodes": r.get("number_of_episodes"),
        "status": r.get("status") or "",
    }
    
def get_tv_watch_providers(tmdb_id: int, region: str = "BR") -> dict:
    url = f"{BASE_URL}/tv/{tmdb_id}/watch/providers"
    params = {"api_key": settings.TMDB_API_KEY}
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()
    results = data.get("results", {}) or {}
    country = results.get(region, {}) or {}
    
    def _map_list(key: str) -> list[dict]:
        items = country.get(key, []) or []
        return [{
            "name": p.get("provider_name") or "",
            "logo_url": _img(p.get("logo_path")),
        } for p in items]
        
    return {
        "link": country.get("link") or "",
        "flatrate": _map_list("flatrate"),
        "rent": _map_list("rent"),
        "buy": _map_list("buy"),
    }
    
def get_trending_tv() -> list[dict]:
    url = f"{BASE_URL}/trending/tv/day"
    params = {"api_key": settings.TMDB_API_KEY, "language": "pt-BR"}
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()

    results = []
    for r in data.get("results", []):
        results.append({
            "tmdb_id": r.get("id"),
            "name": r.get("name") or "",
            "first_air_date": r.get("first_air_date") or "",
            "rating": r.get("vote_average"),
            "poster_url": _img(r.get("poster_path")),
        })
    return results

def get_trending_movies(region: str = "BR") -> list[dict]:
    
    url = f"{BASE_URL}/trending/movie/day"
    params = {
        "api_key": settings.TMDB_API_KEY,
        "language": "pt-BR",
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()
    
    results = []
    for r in data.get("results", []):
        results.append({
            "tmdb_id": r.get("id"),
            "title": r.get("title") or "",
            "release_date": r.get("release_date") or "",
            "rating": r.get("vote_average"),
            "poster_url": _img(r.get("poster_path")),
        })
    return results
