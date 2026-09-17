from pydantic import BaseModel,EmailStr

class UserBase(BaseModel):
    email:EmailStr

class UserCreate(UserBase):
    password:str

class UserResponse(UserBase):
    id:int
    is_active:bool
    class config:
        from_attributes=True

class UserRegistrationResponse(BaseModel):
    message:str
    user:UserResponse

class Msg(BaseModel):
    message:str

class ResetPassword(BaseModel):
    token:str
    new_password:str

class ChangePassword(BaseModel):
    current_password:str
    new_password:str
