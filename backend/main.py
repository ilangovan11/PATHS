"""PATHS backend entry point.

Run:  python main.py        (dev server on 127.0.0.1:8000)
Deploy: uvicorn api.app:app  (see backend/Dockerfile)
"""

import uvicorn

from api.app import app

if __name__ == "__main__":
    uvicorn.run("api.app:app", host="127.0.0.1", port=8000, reload=False)