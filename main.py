from api.app import app
from db.database import engine
from db.models import Base
import uvicorn

Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    uvicorn.run("api.app:app", host="127.0.0.1", port=8000, reload=True)