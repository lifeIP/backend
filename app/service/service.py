from fastapi import HTTPException, status
from fastapi_jwt_auth import AuthJWT


def auth(Authorize:AuthJWT):
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    current_user=Authorize.get_jwt_identity() 
    return current_user