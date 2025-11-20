from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from config import settings

security = HTTPBearer(auto_error=False)

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )

        user_id = payload.get("sub")  # 👍 correct Supabase user ID field
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated"),
            "raw": payload
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def optional_auth(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials is None:
        return None
    return verify_token(credentials)
