"""Minimal FastAPI shim exposing core MemPalace MCP tools."""

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

DEFAULT_PALACE_PATH = "/Users/lexa/Desktop/lexa/omega/omega-palace"
PALACE_ENV = "MEMPALACE_PALACE"
PALACE_PATH_ENV = "MEMPALACE_PALACE_PATH"

_palace_path = (
    os.environ.get(PALACE_ENV)
    or os.environ.get(PALACE_PATH_ENV)
    or DEFAULT_PALACE_PATH
)
os.environ[PALACE_PATH_ENV] = _palace_path
_palace_dir = Path(_palace_path)
_palace_error = None

try:
    from mempalace.mcp_server import (
        tool_add_drawer,
        tool_list_rooms,
        tool_list_wings,
        tool_search,
        tool_status,
    )
except Exception as exc:  # pragma: no cover - startup guard
    _palace_error = str(exc)

app = FastAPI(title="mempalace-sync host")


def _palace_available():
    return _palace_error is None and _palace_dir.exists()


def _body(request: Request):
    async def inner():
        try:
            data = await request.json()
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {}

    return inner()


def _unavailable_response():
    detail = _palace_error or "palace not available"
    return JSONResponse(status_code=503, content={"error": detail})


def _call(handler, payload=None):
    if not _palace_available():
        return _unavailable_response()
    try:
        payload = payload or {}
        return handler(**payload) if payload else handler()
    except Exception as exc:  # pragma: no cover - passthrough guard
        return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/")
async def root_status():
    ok = _palace_available()
    body = {
        "service": "mempalace-sync host",
        "palace_path": _palace_path,
        "ok": ok,
    }
    if _palace_error:
        body["error"] = _palace_error
    return body


@app.post("/v1/tools/mempalace_status")
async def mempalace_status(request: Request):
    await _body(request)
    return _call(tool_status)


@app.post("/v1/tools/mempalace_list_wings")
async def mempalace_list_wings(request: Request):
    await _body(request)
    return _call(tool_list_wings)


@app.post("/v1/tools/mempalace_list_rooms")
async def mempalace_list_rooms(request: Request):
    payload = await _body(request)
    handler_args = {}
    wing = payload.get("wing")
    if wing:
        handler_args["wing"] = wing
    return _call(tool_list_rooms, handler_args)


@app.post("/v1/tools/mempalace_search")
async def mempalace_search(request: Request):
    payload = await _body(request)
    query = payload.get("query")
    if not query:
        return JSONResponse(status_code=400, content={"error": "missing query"})
    handler_args = {
        "query": query,
        "limit": int(payload.get("limit", 5) or 5),
        "wing": payload.get("wing"),
        "room": payload.get("room"),
    }
    if handler_args["limit"] <= 0:
        handler_args["limit"] = 5
    return _call(tool_search, handler_args)


@app.post("/v1/tools/mempalace_add_drawer")
async def mempalace_add_drawer(request: Request):
    payload = await _body(request)
    required = ["wing", "room", "content"]
    missing = [field for field in required if not payload.get(field)]
    if missing:
        return JSONResponse(
            status_code=400,
            content={"error": f"missing fields: {', '.join(missing)}"},
        )
    handler_args = {
        "wing": payload["wing"],
        "room": payload["room"],
        "content": payload["content"],
    }
    if payload.get("source_file"):
        handler_args["source_file"] = payload["source_file"]
    handler_args["added_by"] = payload.get("added_by") or "mempalace-sync"
    return _call(tool_add_drawer, handler_args)
