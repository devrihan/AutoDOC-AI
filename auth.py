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
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_aud": False}
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated"),
            "token": token, 
            "raw": payload
        }

    except JWTError as e:
        print(f"JWT Verification Error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def optional_auth(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials is None:
        return None
    return verify_token(credentials)