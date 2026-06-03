# WEBSOCKETS - FastAPI Realtime

## Stack

| Lib                    | Propósito                          |
| ---------------------- | ---------------------------------- |
| **FastAPI WebSockets** | Built-in                           |
| **python-socketio**    | Alternativa (Socket.io compatible) |

## Estrutura

```
app/
├── websockets/
│   ├── __init__.py
│   ├── manager.py         # Connection manager
│   └── handlers.py        # Event handlers
└── routers/
    └── ws.py              # WebSocket routes
```

## Connection Manager

```python
# app/websockets/manager.py
import logging
from fastapi import WebSocket
from typing import Dict, Set

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: str, message: dict):
        if room_id in self.active_connections:
            dead: list[WebSocket] = []
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead.append(connection)
            for ws in dead:
                self.active_connections[room_id].discard(ws)

    async def send_personal(self, websocket: WebSocket, message: dict):
        await websocket.send_json(message)


manager = ConnectionManager()
```

## WebSocket Router

```python
# app/routers/ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.websockets.manager import manager
from app.dependencies.auth import get_current_user_ws

router = APIRouter()


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
):
    # ✅ Aceitar a ligação primeiro — necessário para trocar mensagens de auth
    # NUNCA usar query param (?token=...) — fica exposto em logs de Nginx/proxy
    # Cookies httpOnly não funcionam em WebSockets nativos → usar handshake por mensagem
    await websocket.accept()

    # Aguardar primeiro frame com token de autenticação
    try:
        auth_data = await websocket.receive_json()
    except Exception:
        await websocket.close(code=4001)
        return

    if auth_data.get("type") != "auth" or not auth_data.get("token"):
        await websocket.close(code=4001)
        return

    # Validar token
    from app.core.security import verify_access_token
    payload = verify_access_token(auth_data["token"])
    if not payload:
        await websocket.close(code=4003)
        return

    manager.add(websocket, room_id)

    try:
        while True:
            data = await websocket.receive_json()

            # Handle diferentes tipos de mensagem
            if data.get("type") == "message":
                await manager.broadcast(room_id, {
                    "type": "message",
                    "content": data["content"],
                    "user_id": data.get("user_id"),
                })
            elif data.get("type") == "typing":
                await manager.broadcast(room_id, {
                    "type": "typing",
                    "user_id": data.get("user_id"),
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast(room_id, {
            "type": "user_left",
            "room_id": room_id,
        })
```

## Registar no Main

```python
# app/main.py
from app.routers import ws

app.include_router(ws.router, tags=["WebSocket"])
```

## Broadcast de Endpoint REST

```python
# app/routers/messages.py
from fastapi import APIRouter, Depends
from app.websockets.manager import manager

router = APIRouter()


@router.post("/rooms/{room_id}/messages")
async def send_message(room_id: str, message: MessageCreate):
    # Guardar mensagem no DB...
    saved = await message_service.create(room_id, message)

    # Broadcast via WebSocket
    await manager.broadcast(room_id, {
        "type": "new_message",
        "data": saved.dict(),
    })

    return saved
```

## Frontend: React Hook

Para o lado React, usar o padrão definido em **[18-websockets](../../../react-enterprise-modular/18-websockets/SKILL.md)** do agente React: `getToken` como função e autenticação via primeiro frame após ligação.

```typescript
// hooks/useWebSocket.ts — padrão seguro (sem token em URL)
import { useEffect, useState, useRef } from "react";

export function useWebSocket<T>(roomId: string, getToken: () => string | null) {
  const [messages, setMessages] = useState<T[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Token NUNCA vai para a URL — exporia o token em logs de servidor
    const ws = new WebSocket(`${import.meta.env.VITE_WS_URL}/ws/${roomId}`);

    ws.onopen = () => {
      // Autenticar via primeiro frame após ligação
      const token = getToken();
      if (token) {
        ws.send(JSON.stringify({ type: "auth", token }));
      }
      setIsConnected(true);
    };

    ws.onclose = () => setIsConnected(false);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages((prev) => [...prev, data]);
    };

    wsRef.current = ws;

    return () => ws.close();
  }, [roomId, getToken]);

  const send = (data: object) => {
    wsRef.current?.send(JSON.stringify(data));
  };

  return { messages, isConnected, send };
}
```

## Regras

| Regra                   | Descrição                    |
| ----------------------- | ---------------------------- |
| Connection Manager      | Singleton para rooms         |
| Auth via primeiro frame | Token em `{ type: "auth", token }` — NUNCA em query param (?token=...) |
| wss:// em produção      | Token viajaria em plaintext com ws://  |
| try/except em broadcast | Conexões podem falhar        |
| JSON para mensagens     | `send_json` / `receive_json` |
| Cleanup em disconnect   | Remover da room              |
