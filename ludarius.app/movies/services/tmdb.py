import requests 
from django.conf import settings

BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/w500"

def _img(path: str | None) -> str:
    if not path:
        return ""
    return f"{IMG_BASE}{path}"

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
