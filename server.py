import os
import re
import json
import asyncio
import subprocess
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from dotenv import load_dotenv
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import HumanMessage, AIMessage

from desktop_tools import (
    try_direct_routing, 
    desktop_tools, 
    set_system_volume, 
    mute_system_sound, 
    take_screenshot, 
    toggle_dark_mode, 
    control_media, 
    play_music, 
    open_app, 
    close_app,
    get_battery_status,
    get_system_specs
)
from main import agent_executor, parse_research_response, extract_text_content, ResearchResponse

load_dotenv()

# In-memory rolling conversation history
chat_history: List[Any] = []
MAX_HISTORY_MESSAGES = 12

# Connection Manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

ws_manager = ConnectionManager()

class StreamCallbackHandler(BaseCallbackHandler):
    """Broadcasts real-time tool execution notifications via WebSocket."""
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        tool_name = serialized.get("name", "Tool")
        clean_input = str(input_str).strip()
        if len(clean_input) > 80:
            clean_input = clean_input[:77] + "..."
        asyncio.run_coroutine_threadsafe(
            ws_manager.broadcast({
                "type": "tool_start",
                "tool": tool_name,
                "input": clean_input
            }),
            self.loop
        )

    def on_tool_end(self, output: Any, **kwargs: Any) -> None:
        clean_out = str(output).strip()
        if len(clean_out) > 120:
            clean_out = clean_out[:117] + "..."
        asyncio.run_coroutine_threadsafe(
            ws_manager.broadcast({
                "type": "tool_end",
                "output": clean_out
            }),
            self.loop
        )

    def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        asyncio.run_coroutine_threadsafe(
            ws_manager.broadcast({
                "type": "tool_error",
                "error": str(error)
            }),
            self.loop
        )

# Request / Response Schemas
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User prompt or voice command")

class VolumeRequest(BaseModel):
    level: Optional[int] = Field(None, ge=0, le=100)
    direction: Optional[str] = Field(None, description="'up' or 'down'")

class MediaRequest(BaseModel):
    action: str = Field(..., description="'play', 'pause', 'next', 'previous', 'random', or 'song'")
    song: Optional[str] = Field(None, description="Song title if action is 'song'")

class QuickActionRequest(BaseModel):
    action: str = Field(..., description="'screenshot', 'dark_mode', 'lock_screen', 'mute', 'unmute'")

class AppRequest(BaseModel):
    action: str = Field("open", description="'open' or 'close'")
    app_name: str = Field(..., description="App name or URL")

# Helper for live system status
def fetch_live_system_status() -> dict:
    """Queries macOS live telemetry (battery, volume, mute state, appearance, hardware)."""
    status = {
        "battery": {"percent": 100, "charging": False, "raw": "N/A"},
        "volume": {"level": 50, "muted": False},
        "dark_mode": True,
        "specs": "macOS M-Series",
    }

    # 1. Battery via pmset
    try:
        res = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True, timeout=2)
        out = res.stdout
        pct_match = re.search(r"(\d+)%", out)
        if pct_match:
            status["battery"]["percent"] = int(pct_match.group(1))
        status["battery"]["charging"] = "charging" in out.lower() or "ac attached" in out.lower()
        status["battery"]["raw"] = out.strip().split("\n")[-1] if out else "Unknown"
    except Exception:
        pass

    # 2. Volume & Mute via osascript
    try:
        res = subprocess.run(
            ["osascript", "-e", "output volume of (get volume settings) & \",\" & output muted of (get volume settings)"],
            capture_output=True, text=True, timeout=2
        )
        parts = res.stdout.strip().split(",")
        if len(parts) == 2:
            status["volume"]["level"] = int(parts[0].strip()) if parts[0].strip().isdigit() else 50
            status["volume"]["muted"] = parts[1].strip().lower() == "true"
    except Exception:
        pass

    # 3. Dark mode state
    try:
        res = subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to tell appearance preferences to return dark mode'],
            capture_output=True, text=True, timeout=2
        )
        status["dark_mode"] = res.stdout.strip().lower() == "true"
    except Exception:
        pass

    # 4. Chip & Specs
    try:
        chip_res = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, timeout=2)
        chip = chip_res.stdout.strip() or "Apple Silicon"
        status["specs"] = chip
    except Exception:
        pass

    return status

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    print("🚀 MacOS AI Agent Web Server initialized at http://localhost:8000")
    yield
    # Shutdown actions
    print("🛑 Server shutting down.")

app = FastAPI(
    title="macOS AI Agent Web API",
    description="Full-stack AI Agent and macOS Desktop Automation System",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST Endpoints
@app.get("/api/status")
async def get_status():
    """Returns real-time macOS system telemetry."""
    return fetch_live_system_status()

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Executes a natural language user query or voice command."""
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    loop = asyncio.get_event_loop()

    # 1. Check Sub-50ms Instant Direct Router first
    direct_result = try_direct_routing(query)
    if direct_result:
        structured = {
            "topic": direct_result.get("topic", query),
            "summary": direct_result.get("summary", ""),
            "sources": direct_result.get("sources", []),
            "tools_used": direct_result.get("tools_used", ["Instant Direct Router"]),
            "is_direct": True
        }
        chat_history.append(HumanMessage(content=query))
        chat_history.append(AIMessage(content=structured["summary"]))
        if len(chat_history) > MAX_HISTORY_MESSAGES:
            del chat_history[:len(chat_history) - MAX_HISTORY_MESSAGES]

        await ws_manager.broadcast({
            "type": "chat_response",
            "query": query,
            "response": structured
        })
        return structured

    # 2. Route to Gemini Reasoning Agent
    callback = StreamCallbackHandler(loop)
    await ws_manager.broadcast({"type": "agent_start", "query": query})

    def run_agent():
        raw_res = agent_executor.invoke(
            {"query": query, "chat_history": chat_history},
            config={"callbacks": [callback]}
        )
        return extract_text_content(raw_res.get("output", ""))

    try:
        raw_output = await asyncio.to_thread(run_agent)
        parsed = parse_research_response(raw_output, query=query)
        structured = {
            "topic": parsed.topic,
            "summary": parsed.summary,
            "sources": parsed.sources,
            "tools_used": parsed.tools_used,
            "is_direct": False
        }
        chat_history.append(HumanMessage(content=query))
        chat_history.append(AIMessage(content=parsed.summary))
        if len(chat_history) > MAX_HISTORY_MESSAGES:
            del chat_history[:len(chat_history) - MAX_HISTORY_MESSAGES]

        await ws_manager.broadcast({
            "type": "chat_response",
            "query": query,
            "response": structured
        })
        return structured
    except Exception as e:
        await ws_manager.broadcast({"type": "agent_error", "error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/action/volume")
async def volume_endpoint(req: VolumeRequest):
    """Direct volume adjustment endpoint."""
    if req.level is not None:
        msg = set_system_volume.func(req.level)
        return {"status": "success", "message": msg, "level": req.level}
    
    # Relative up/down
    curr = fetch_live_system_status()
    current_vol = curr["volume"]["level"]
    if req.direction == "up":
        new_vol = min(100, current_vol + 15)
    else:
        new_vol = max(0, current_vol - 15)
    
    msg = set_system_volume.func(new_vol)
    return {"status": "success", "message": msg, "level": new_vol}

@app.post("/api/action/media")
async def media_endpoint(req: MediaRequest):
    """Direct music and media control endpoint."""
    act = req.action.lower()
    if act == "random":
        res = play_music.func("")
        return {"status": "success", "message": res}
    if act == "song" and req.song:
        res = play_music.func(req.song)
        return {"status": "success", "message": res}
    
    res = control_media.func(act)
    return {"status": "success", "message": res}

@app.post("/api/action/quick")
async def quick_action_endpoint(req: QuickActionRequest):
    """Triggers instant system actions (screenshot, dark mode, mute, lock)."""
    act = req.action.lower()
    if act == "screenshot":
        res = take_screenshot.func()
        return {"status": "success", "message": res}
    if act == "dark_mode":
        res = toggle_dark_mode.func()
        return {"status": "success", "message": res}
    if act == "mute":
        res = mute_system_sound.func(True)
        return {"status": "success", "message": res}
    if act == "unmute":
        res = mute_system_sound.func(False)
        return {"status": "success", "message": res}
    if act == "lock_screen":
        subprocess.run(["pmset", "displaysleepnow"])
        return {"status": "success", "message": "macOS display locked / sleeping."}
    
    raise HTTPException(status_code=400, detail=f"Unknown action: {act}")

@app.post("/api/action/app")
async def app_endpoint(req: AppRequest):
    """Opens or closes desktop apps or web URLs."""
    if req.action == "close":
        res = close_app.func(req.app_name)
    else:
        res = open_app.func(req.app_name)
    return {"status": "success", "message": res}

@app.get("/api/history")
async def get_history():
    """Returns conversation history."""
    items = []
    for msg in chat_history:
        sender = "user" if isinstance(msg, HumanMessage) else "agent"
        items.append({"sender": sender, "content": msg.content})
    return {"history": items}

@app.post("/api/clear")
async def clear_memory():
    """Clears multi-turn conversation memory."""
    chat_history.clear()
    return {"status": "success", "message": "Conversation memory cleared."}

# WebSocket for real-time live events & voice sync
@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send initial welcome & status
        status = fetch_live_system_status()
        await websocket.send_json({"type": "init", "status": status})
        while True:
            data = await websocket.receive_text()
            # Handle incoming ping / messages if needed
            try:
                msg = json.loads(data)
                if msg.get("action") == "ping":
                    await websocket.send_json({"type": "pong"})
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

# Mount static files and root fallback
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse({"status": "running", "message": "Static frontend not yet generated."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
