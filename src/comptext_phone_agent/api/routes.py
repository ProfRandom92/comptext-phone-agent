from __future__ import annotations
from pathlib import Path
import json
import secrets
from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Route
from ..storage.analyzer import StorageAnalyzer
from ..storage.duplicates import DuplicateDetector
from .schemas import ScanRequest


def require_token(request: Request) -> None:
    supplied = request.headers.get("x-comptext-token", "")
    expected = request.app.state.session_token
    if not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=403, detail="invalid local session token")


def require_csrf(request: Request) -> None:
    supplied = request.headers.get("x-comptext-csrf", "")
    expected = request.app.state.csrf_token
    if not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=403, detail="invalid CSRF token")


def _root(request: Request, value: str | None) -> Path:
    root = Path(value or request.app.state.config.storage_roots[0]).expanduser().resolve()
    configured = [Path(x).expanduser().resolve() for x in request.app.state.config.storage_roots]
    if not any(root == allowed or allowed in root.parents for allowed in configured):
        raise HTTPException(status_code=403, detail="path outside configured storage roots")
    return root


def _protected(request: Request) -> None:
    require_token(request)


def home(request: Request) -> HTMLResponse:
    del request
    return HTMLResponse("""<!doctype html><html><head><meta name=viewport content='width=device-width,initial-scale=1'>
<title>CompText Phone Agent</title><style>
body{font-family:system-ui;background:#111827;color:#f3f4f6;max-width:980px;margin:auto;padding:1rem}button,input{font:inherit;padding:.7rem;border-radius:.6rem;border:1px solid #4b5563;background:#1f2937;color:#fff}button{cursor:pointer}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem}.card{background:#1f2937;border:1px solid #374151;border-radius:1rem;padding:1rem;overflow:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.8rem}.danger{color:#fca5a5}.ok{color:#86efac}</style></head><body>
<h1>CompText Phone Agent</h1><p>Lokales Dashboard auf 127.0.0.1. Keine externen CDNs.</p>
<div class=card><input id=token type=password placeholder='Session token'><input id=path placeholder='Storage path (optional)'><button onclick=loadAll()>Ansichten laden</button><button onclick=scan()>Scan (POST)</button><span id=state></span></div>
<div class=grid id=grid></div><script>
let csrf=''; const names=['status','storage','duplicates','plans','approvals','trash','backups','audit','reports'];
const headers=()=>({'X-CompText-Token':token.value}); async function get(n){let u='/api/'+n;if(['storage','duplicates'].includes(n)&&path.value)u+='?path='+encodeURIComponent(path.value);let r=await fetch(u,{headers:headers()});return [r.status,await r.json()]}
async function loadAll(){state.textContent=' Lädt…';let c=await fetch('/api/csrf',{headers:headers()});if(!c.ok){state.textContent=' Zugriff verweigert';return}csrf=(await c.json()).token;grid.innerHTML='';for(const n of names){let [s,d]=await get(n);grid.innerHTML+=`<section class=card><h2>${n}</h2><pre>${JSON.stringify(d,null,2)}</pre></section>`}state.textContent=' Bereit'}
async function scan(){if(!csrf)await loadAll();let r=await fetch('/api/scan',{method:'POST',headers:{...headers(),'X-CompText-CSRF':csrf,'Content-Type':'application/json'},body:JSON.stringify({path:path.value})});let d=await r.json();alert(r.status+' '+JSON.stringify(d).slice(0,500))}
</script></body></html>""")


def status(request: Request) -> JSONResponse:
    _protected(request)
    return JSONResponse({"ok": True, "host": request.app.state.config.dashboard.host, "mode": request.app.state.config.mode.value})


def storage(request: Request) -> JSONResponse:
    _protected(request)
    result = request.app.state.scanner.scan(_root(request, request.query_params.get("path")))
    analyzer = StorageAnalyzer(result)
    return JSONResponse({"root": result.root, "total_files": result.total_files, "total_size": result.total_size, "largest": [x.to_dict() for x in analyzer.largest_files(30)], "types": analyzer.by_type()})


def duplicates(request: Request) -> JSONResponse:
    _protected(request)
    result = request.app.state.scanner.scan(_root(request, request.query_params.get("path")))
    return JSONResponse([x.to_dict() for x in DuplicateDetector().find(result, verify=True)])


def audit(request: Request) -> JSONResponse:
    _protected(request)
    raw_limit = request.query_params.get("limit", "100")
    try:
        limit = int(raw_limit)
    except ValueError as error:
        raise HTTPException(status_code=400, detail="invalid audit limit") from error
    return JSONResponse(request.app.state.audit.list(max(1, min(limit, 500))))


def trash(request: Request) -> JSONResponse:
    _protected(request)
    return JSONResponse(request.app.state.trash.list())


def _plans(request: Request) -> list[dict]:
    with request.app.state.database.connect() as connection:
        return [json.loads(row["body"]) for row in connection.execute("SELECT body FROM plans ORDER BY created_at DESC LIMIT 200")]


def plans(request: Request) -> JSONResponse:
    _protected(request)
    return JSONResponse(_plans(request))


def approvals(request: Request) -> JSONResponse:
    _protected(request)
    with request.app.state.database.connect() as connection:
        values = [dict(row) for row in connection.execute("SELECT id,plan_hash,created_at,expires_at,risk,consumed_at,revoked FROM approvals ORDER BY created_at DESC LIMIT 200")]
    return JSONResponse(values)


def backups(request: Request) -> JSONResponse:
    _protected(request)
    values = [plan for plan in _plans(request) if any(action.get("action") == "upload" for action in plan.get("actions", []))]
    return JSONResponse(values)


def reports(request: Request) -> JSONResponse:
    _protected(request)
    folder = request.app.state.data_dir / "reports"
    if not folder.exists():
        return JSONResponse([])
    values = [{"name": p.name, "size": p.stat().st_size, "mtime": p.stat().st_mtime} for p in sorted(folder.iterdir(), reverse=True) if p.is_file()]
    return JSONResponse(values)


async def scan(request: Request) -> Response:
    _protected(request)
    require_csrf(request)
    try:
        payload = ScanRequest.parse_obj(await request.json())
    except (ValidationError, ValueError, TypeError) as error:
        detail = json.loads(error.json()) if isinstance(error, ValidationError) else [{"msg": "invalid JSON request"}]
        return JSONResponse({"detail": detail}, status_code=422)
    result = request.app.state.scanner.scan(_root(request, payload.path))
    analyzer = StorageAnalyzer(result)
    return JSONResponse({"root": result.root, "total_files": result.total_files, "total_size": result.total_size, "largest": [x.to_dict() for x in analyzer.largest_files(30)], "types": analyzer.by_type()})


def csrf(request: Request) -> JSONResponse:
    _protected(request)
    return JSONResponse({"token": request.app.state.csrf_token})


routes = [
    Route("/", home, methods=["GET"]),
    Route("/api/status", status, methods=["GET"]),
    Route("/api/storage", storage, methods=["GET"]),
    Route("/api/duplicates", duplicates, methods=["GET"]),
    Route("/api/audit", audit, methods=["GET"]),
    Route("/api/trash", trash, methods=["GET"]),
    Route("/api/plans", plans, methods=["GET"]),
    Route("/api/approvals", approvals, methods=["GET"]),
    Route("/api/backups", backups, methods=["GET"]),
    Route("/api/reports", reports, methods=["GET"]),
    Route("/api/scan", scan, methods=["POST"]),
    Route("/api/csrf", csrf, methods=["GET"]),
]
