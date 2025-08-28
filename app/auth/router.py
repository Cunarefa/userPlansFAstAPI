from fastapi import Depends

from app.auth.service import create_access_token, get_current_user
from app.main import app


@app.post("/token")
def login():
    access_token = create_access_token(data={"sub": "testuser"})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
def read_users_me(username: str = Depends(get_current_user)):
    return {"username": username}