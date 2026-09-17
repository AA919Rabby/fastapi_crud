from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash


# def get_user_by_email(db:Session,email:str):
#     return db.query(User).filter(User.email==email).first()

def get_user_by_email(db: Session, email: str):
    # Let's print exactly what we are searching for
    print(f"--- DATABASE SEARCHING FOR EMAIL: '{email}' ---")

    user = db.query(User).filter(User.email == email).first()

    # Let's print if we found them or not
    print(f"--- DATABASE FOUND: {user} ---")

    return user

def create_user(db:Session,user:UserCreate):
    hashed_password=get_password_hash(user.password)
    db_user=User(email=user.email,hashed_password=hashed_password,is_active=True)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_id(db:Session,user_id:int):
    return db.query(User).filter(User.id==user_id).first()

def update_user_password(db:Session,db_user:User,new_password:str):
    hashed_password=get_password_hash(new_password)
    db_user.hashed_password=hashed_password
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


