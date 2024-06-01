from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from routes.user import user_router
from routes.auth import auth_router

app = FastAPI()

app.include_router(router=user_router)
app.include_router(router=auth_router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


