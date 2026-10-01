from cache.search_cache import SearchCache

def test_cache(tmp_path):
    c = SearchCache(tmp_path, ttl_hours=1)
    c.put("hello", [{"title":"x"}])
    assert c.get("hello")[0]["title"] == "x"
