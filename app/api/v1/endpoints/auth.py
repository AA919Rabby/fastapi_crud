
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate,UserRegistrationResponse,Msg,ResetPassword,ChangePassword
from app.crud.crud_user import get_user_by_email,create_user
from app.core.database import get_db
from fastapi import Depends,HTTPException,status,APIRouter,BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password,create_access_token,verify_password,create_access_token,create_password_reset_token,verify_password_reset_token
from app.crud.crud_user import get_user_by_email,update_user_password
from app.schemas.token import Token
from app.api.deps import get_current_user
from app.models.user import User



router=APIRouter()

@router.post("/register",response_model=UserRegistrationResponse,status_code=status.HTTP_201_CREATED)
def register_user(user_in:UserCreate,db:Session=Depends(get_db)):
    user=get_user_by_email(db,email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    new_user=create_user(db,user=user_in)
    return {
        "message":"Your account was successfully created",
        "user":new_user
    }


@router.post("/login",response_model=Token)
def login_for_access_token(
    form_data:OAuth2PasswordRequestForm=Depends(),
    db:Session=Depends(get_db)
):
    user=get_user_by_email(db,email=form_data.username)
    if not user or not verify_password(form_data.password,user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate":"Bearer"}
        )
    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Inactive user"
        )
    access_token=create_access_token(subject=user.id)
    return {
        "access_token":access_token,
        "token_type":"bearer"
    }


@router.post("/forget_password",response_model=Msg)
def recover_password(email:str,background_tasks:BackgroundTasks,db:Session=Depends(get_db)):
    user=get_user_by_email(db,email=email)
    if not user:
        return {
            "message":"If that email exists, a password reset link has been sent."
        }
    reset_token=create_password_reset_token(email=email)
    def mock_send_email(email_to:str,token:str):
        print("\n" + "="*50)
        print(f"MOCK EMAIL SENT TO: {email_to}")
        print(f"COPY THIS TOKEN TO TEST RESET: {token}")
        print("="*50 + "\n")
        print("\n" + "="*50)
        print(f"DECODED EMAIL FROM TOKEN: '{email}'")
        print("="*50 + "\n")
    background_tasks.add_task(mock_send_email,email,reset_token)
    return {
        "message":"If that email exists, a password reset link has been sent."
    }

@router.post("/reset_password",response_model=Msg)
def reset_password(body:ResetPassword,db:Session=Depends(get_db)):
    email=verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired token"
        )
    user=get_user_by_email(db,email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found in database"
        )
    if user.is_active is False:
        raise HTTPException(
            status_code=400,
            detail="User is inactive"
        )
    update_user_password(db,db_user=user,new_password=body.new_password)
    return {
        "message":"Password successfully updated"
    }


@router.post("/change_password",response_model=Msg)
def change_password(body:ChangePassword,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if not verify_password(body.current_password,current_user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Invalid password"
        )
    update_user_password(db,db_user=current_user,new_password=body.new_password)
    return {
        "message":"Password successfully updated"
    }


