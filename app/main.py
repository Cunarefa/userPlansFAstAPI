import uvicorn
from fastapi import FastAPI

from app.user_plans_app.routers.credits import router as user_credits
from app.user_plans_app.routers.plans import router as insert_plan

app = FastAPI()

app.include_router(user_credits)
app.include_router(insert_plan)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)