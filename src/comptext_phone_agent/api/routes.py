from __future__ import annotations
from pathlib import Path
import json
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from ..storage.analyzer import StorageAnalyzer
from ..storage.duplicates import DuplicateDetector

router = APIRouter()

def require_token(request: Request, x_comptext_token: str | None = Header(default=None)) -> None:
    if x_comptext_token != request.app.state.session_token:
        raise HTTPException(status_code=403, detail="invalid local session token")

def require_csrf(request: Request, x_comptext_csrf: str | None = Header(default=None)) -> None:
    if x_comptext_csrf != request.app.state.csrf_token:
        raise HTTPException(status_code=403, detail="invalid CSRF token")

def _root(request: Request, value: str | None) -> Path:
    root = Path(value or request.app.state.config.storage_roots[0]).expanduser().resolve()
    configured = [Path(x).expanduser().resolve() for x in request.app.state.config.storage_roots]
    if not any(root == allowed or allowed in root.parents for allowed in configured):
        raise HTTPException(status_code=403, detail="path outside configured storage roots")
    return root

@router.get("/", response_class=HTMLResponse)
def home() -> str:
    return """<!doctype html><html><head><meta name=viewport content='width=device-width,initial-scale=1'>
<title>CompText Phone Agent</title><style>
body{font-family:system-ui;background:#111827;color:#f3f4f6;max-width:980px;margin:auto;padding:1rem}button,input{font:inherit;padding:.7rem;border-radius:.6rem;border:1px solid #4b5563;background:#1f2937;color:#fff}button{cursor:pointer}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem}.card{background:#1f2937;border:1px solid #374151;border-radius:1rem;padding:1rem;overflow:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.8rem}.danger{color:#fca5a5}.ok{color:#86efac}</style></head><body>
<h1>CompText Phone Agent</h1><p>Lokales Dashboard auf 127.0.0.1. Keine externen CDNs.</p>
<div class=card><input id=token type=password placeholder='Session token'><input id=path placeholder='Storage path (optional)'><button onclick=loadAll()>Ansichten laden</button><button onclick=scan()>Scan (POST)</button><span id=state></span></div>
<div class=grid id=grid></div><script>
let csrf=''; const names=['status','storage','duplicates','plans','approvals','trash','backups','audit','reports'];
const headers=()=>({'X-CompText-Token':token.value}); async function get(n){let u='/api/'+n;if(['storage','duplicates'].includes(n)&&path.value)u+='?path='+encodeURIComponent(path.value);let r=await fetch(u,{headers:headers()});return [r.status,await r.json()]}
async function loadAll(){state.textContent=' Lädt…';let c=await fetch('/api/csrf',{headers:headers()});if(!c.ok){state.textContent=' Zugriff verweigert';return}csrf=(await c.json()).token;grid.innerHTML='';for(const n of names){let [s,d]=await get(n);grid.innerHTML+=`<section class=card><h2>${n}</h2><pre>${JSON.stringify(d,null,2)}</pre></section>`}state.textContent=' Bereit'}
async function scan(){if(!csrf)await loadAll();let r=await fetch('/api/scan',{method:'POST',headers:{...headers(),'X-CompText-CSRF':csrf,'Content-Type':'application/json'},body:JSON.stringify({path:path.value})});let d=await r.json();alert(r.status+' '+JSON.stringify(d).slice(0,500))}
</script></body></html>"""

@router.get("/api/status", dependencies=[Depends(require_token)])
def status(request: Request) -> dict:
    return {"ok": True, "host": request.app.state.config.dashboard.host, "mode": request.app.state.config.mode.value}

@router.get("/api/storage", dependencies=[Depends(require_token)])
def storage(request: Request, path: str | None = None) -> dict:
    result = request.app.state.scanner.scan(_root(request, path))
    analyzer = StorageAnalyzer(result)
    return {"root": result.root, "total_files": result.total_files, "total_size": result.total_size, "largest": [x.to_dict() for x in analyzer.largest_files(30)], "types": analyzer.by_type()}

@router.get("/api/duplicates", dependencies=[Depends(require_token)])
def duplicates(request: Request, path: str | None = None) -> list[dict]:
    result = request.app.state.scanner.scan(_root(request, path))
    return [x.to_dict() for x in DuplicateDetector().find(result, verify=True)]

@router.get("/api/audit", dependencies=[Depends(require_token)])
def audit(request: Request, limit: int = 100) -> list[dict]:
    return request.app.state.audit.list(min(limit, 500))

@router.get("/api/trash", dependencies=[Depends(require_token)])
def trash(request: Request) -> list[dict]:
    return request.app.state.trash.list()

@router.get("/api/plans", dependencies=[Depends(require_token)])
def plans(request: Request) -> list[dict]:
    with request.app.state.database.connect() as connection:
        return [json.loads(row["body"]) for row in connection.execute("SELECT body FROM plans ORDER BY created_at DESC LIMIT 200")]

@router.get("/api/approvals", dependencies=[Depends(require_token)])
def approvals(request: Request) -> list[dict]:
    with request.app.state.database.connect() as connection:
        return [dict(row) for row in connection.execute("SELECT id,plan_hash,created_at,expires_at,risk,consumed_at,revoked FROM approvals ORDER BY created_at DESC LIMIT 200")]

@router.get("/api/backups", dependencies=[Depends(require_token)])
def backups(request: Request) -> list[dict]:
    return [plan for plan in plans(request) if any(action.get("action") == "upload" for action in plan.get("actions", []))]

@router.get("/api/reports", dependencies=[Depends(require_token)])
def reports(request: Request) -> list[dict]:
    folder = request.app.state.data_dir / "reports"
    if not folder.exists(): return []
    return [{"name": p.name, "size": p.stat().st_size, "mtime": p.stat().st_mtime} for p in sorted(folder.iterdir(), reverse=True) if p.is_file()]

@router.post("/api/scan", dependencies=[Depends(require_token), Depends(require_csrf)])
async def scan(request: Request) -> dict:
    body = await request.json()
    result = request.app.state.scanner.scan(_root(request, body.get("path")))
    analyzer = StorageAnalyzer(result)
    return {"root": result.root, "total_files": result.total_files, "total_size": result.total_size, "largest": [x.to_dict() for x in analyzer.largest_files(30)], "types": analyzer.by_type()}

@router.get("/api/csrf", dependencies=[Depends(require_token)])
def csrf(request: Request) -> dict:
    return {"token": request.app.state.csrf_token}
