import time
import uuid
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/jaas", tags=["jaas"])

JAAS_APP_ID  = os.getenv("JAAS_APP_ID",  "vpaas-magic-cookie-429e9a26ae1d432a9cd8c51b9081cf3e")
JAAS_KEY_ID  = os.getenv("JAAS_KEY_ID",  "vpaas-magic-cookie-429e9a26ae1d432a9cd8c51b9081cf3e/6578ba")
JAAS_PRIVATE_KEY = os.getenv("JAAS_PRIVATE_KEY", "")


class TokenRequest(BaseModel):
    room: str
    name: str
    email: Optional[str] = ""
    user_id: Optional[str] = ""
    moderator: bool = False


@router.post("/token")
def get_jaas_token(req: TokenRequest):
    if not JAAS_PRIVATE_KEY:
        raise HTTPException(status_code=500, detail="JaaS private key not configured")

    try:
        import jwt as pyjwt
    except ImportError:
        raise HTTPException(status_code=500, detail="PyJWT not installed")

    now = int(time.time())

    payload = {
        "aud": "jitsi",
        "iss": "chat",
        "iat": now,
        "exp": now + 7200,   # 2 horas
        "nbf": now - 10,
        "sub": JAAS_APP_ID,
        "context": {
            "features": {
                "livestreaming": False,
                "file-upload": False,
                "outbound-call": False,
                "sip-outbound-call": False,
                "transcription": False,
                "list-visitors": False,
                "recording": False,
                "flip": False,
            },
            "user": {
                "hidden-from-recorder": False,
                "moderator": req.moderator,
                "name": req.name,
                "id": req.user_id or str(uuid.uuid4()),
                "avatar": "",
                "email": req.email or "",
            },
        },
        "room": "*",
    }

    private_key = JAAS_PRIVATE_KEY.replace("\\n", "\n")

    token = pyjwt.encode(
        payload,
        private_key,
        algorithm="RS256",
        headers={"kid": JAAS_KEY_ID},
    )

    room_url = f"https://8x8.vc/{JAAS_APP_ID}/{req.room}?jwt={token}"
    return {"token": token, "room_url": room_url}
