import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Body, status, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import Annotated

from teler.streams import StreamConnector, StreamOp, StreamType
from teler import AsyncClient, CallFlow

router = APIRouter()
logger = logging.getLogger(__name__)

# Global variables
ELEVENLABS_AGENT_ID = "agent_0501k6d1c9fhejpb7rfcs2whhgqt"
ELEVENLABS_WEBSOCKET_URL = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={ELEVENLABS_AGENT_ID}"

TELER_API_KEY = "9b5c251fbe0e8c1a3034ec0ec55d8bb3b64f97c64670850eaf3a604c9881549e"
# BACKEND_DOMAIN = "hypobranchial-arlinda-homelike.ngrok-free.dev"
BACKEND_DOMAIN = "voiceaiagent.emotorad.com"
FROM_NUMBER = "+918065193797"
TO_NUMBER = "+919156188065"


class CallFlowRequest(BaseModel):
    call_id: str
    account_id: str
    from_number: str
    to_number: str

async def call_stream_handler(message: str):
    msg = json.loads(message)
    if msg["type"] == "audio":
        payload = json.dumps({"user_audio_chunk": msg["data"]["audio_b64"]})
        return (payload, StreamOp.RELAY)
    return ({}, StreamOp.PASS)

def remote_stream_handler():
    chunk_id = 1

    async def handler(message: str):
        nonlocal chunk_id
        msg = json.loads(message)
        if msg["type"] == "audio":
            payload = json.dumps(
                {
                    "type": "audio",
                    "audio_b64": msg["audio_event"]["audio_base_64"],
                    "chunk_id": chunk_id,
                }
            )
            chunk_id += 1
            return (payload, StreamOp.RELAY)
        elif msg["type"] == "interruption":
            payload = json.dumps({"type": "clear"})
            return (payload, StreamOp.RELAY)
        return ({}, StreamOp.PASS)

    return handler

connector = StreamConnector(
    stream_type=StreamType.BIDIRECTIONAL,
    remote_url=ELEVENLABS_WEBSOCKET_URL,
    call_stream_handler=call_stream_handler,
    remote_stream_handler=remote_stream_handler(),
)

@router.post("/flow", status_code=status.HTTP_200_OK, include_in_schema=False)
async def stream_flow(payload: CallFlowRequest):
    """
    Build and return Stream flow.
    """
    stream_flow = CallFlow.stream(
        ws_url=f"wss://{BACKEND_DOMAIN}/media-stream",
        chunk_size=500,
        record=True
    )
    return JSONResponse(stream_flow)

@router.post("/webhook", status_code=status.HTTP_200_OK, include_in_schema=False)
async def webhook_receiver(data: Annotated[dict, Body()]):
    logger.info(f"--------Webhook Payload-------- {data}")
    return JSONResponse(content="Webhook received.")

@router.get("/initiate-call", status_code=status.HTTP_200_OK)
async def initiate_call():
    """
    Initiate a call using Teler SDK.
    """
    try:
        async with AsyncClient(api_key=TELER_API_KEY, timeout=10) as client:
            call = await client.calls.create(
                from_number=f"{FROM_NUMBER}",
                to_number=f"{TO_NUMBER}",
                flow_url=f"https://{BACKEND_DOMAIN}/flow",
                status_callback_url=f"https://{BACKEND_DOMAIN}/webhook",
                record=True,
            )
            logger.info(f"Call created: {call}")
        return JSONResponse(content={"success": True})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create call.")

@router.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected.")
    await connector.bridge_stream(websocket)