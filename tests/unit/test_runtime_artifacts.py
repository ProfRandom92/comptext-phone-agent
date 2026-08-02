from comptext_phone_agent.audit.database import Database
from comptext_phone_agent.runtime.artifacts import ArtifactStore
from comptext_phone_agent.runtime.store import RuntimeStore

def test_artifact_projection_redacts_paths_and_wifi(tmp_path):
    db=Database(tmp_path/'s.db'); run=RuntimeStore(db).create_run('s','g')
    root=tmp_path/'phone'; root.mkdir()
    store=ArtifactStore(db,root)
    payload={'absolute_path':str(root/'x'), 'files':[str(root/'a'),str(root/'b')], 'bssid':'secret','ip':'1.2.3.4','ssid':'ok'}
    art=store.put(run.id,'scan',payload); projected=store.project_for_model(art.payload,max_items=1)
    assert 'absolute_path' not in projected and 'bssid' not in projected and 'ip' not in projected
    assert projected['files']==['a'] and projected['ssid']=='ok'
