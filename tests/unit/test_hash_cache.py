from comptext_phone_agent.audit.database import Database
from comptext_phone_agent.storage.hash_cache import HashCache

def test_hash_cache_invalidates_on_change(tmp_path):
    db=Database(tmp_path/'state.db'); cache=HashCache(db.path); p=tmp_path/'a.bin'; p.write_bytes(b'a')
    cache.put(p,'sha256','one'); assert cache.get(p,'sha256')=='one'
    p.write_bytes(b'changed'); assert cache.get(p,'sha256') is None

def test_hash_cache_prunes_missing(tmp_path):
    db=Database(tmp_path/'state.db'); cache=HashCache(db.path); p=tmp_path/'a'; p.write_bytes(b'x'); cache.put(p,'partial','x'); p.unlink(); assert cache.prune_missing()==1
