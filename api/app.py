from fastapi import FastAPI
from api.routes import router

app = FastAPI(title="PATHS: The Coordinate Engine")

app.include_router(router)
