from __future__ import annotations
import socket
from urllib.parse import urlparse

def diagnose_orchestrator(config, catalog) -> dict:
    data={
        'enabled':config.enabled,
        'router_mode':config.router_mode,
        'router_model':config.router_model,
        'planner_model':config.planner_model,
        'minimum_confidence':config.minimum_confidence,
        'action_count':len(catalog.names()),
        'actions':list(catalog.names()),
        'broker_reachable':None,
    }
    if config.router_mode=='broker':
        parsed=urlparse(config.router_base_url)
        port=parsed.port or (443 if parsed.scheme=='https' else 80)
        try:
            with socket.create_connection((parsed.hostname,port),timeout=1): data['broker_reachable']=True
        except OSError: data['broker_reachable']=False
    return data
