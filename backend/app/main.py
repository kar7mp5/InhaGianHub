from fastapi import FastAPI
from contextlib import asynccontextmanager
from config.db import engine
from models import Base
from controllers import reservation_controller

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler to manage startup and shutdown tasks.
    """
    # 🚀 Startup: Drop and recreate tables (for development)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # 🔻 Shutdown: Nothing for now

app = FastAPI(lifespan=lifespan)

app.include_router(reservation_controller.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
