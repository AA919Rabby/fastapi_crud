from fastapi import Depends,HTTPException,status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from app.core.config import settings
from app.core.database import get_db
from app.crud.crud_user import get_user_by_id
from app.models.user import User


oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

def get_current_user(db:Session=Depends(get_db),token:str=Depends(oauth2_scheme))->User:
    credentials_exception=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate":"Bearer"}
    )
    try:
        payload=jwt.decode(token,settings.SECRET_KEY,algorithms=settings.ALGORITHM)
        user_id=payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user=get_user_by_id(db,user_id=int(user_id))
    if user is None:
        raise credentials_exception
    return user
