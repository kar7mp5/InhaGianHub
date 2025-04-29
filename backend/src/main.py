from fastapi import FastAPI
from contextlib import asynccontextmanager
from config.db import engine
from models import Base
from controllers import reservation_controller
from fastapi.middleware.cors import CORSMiddleware

import threading
import time
import requests

# List of facilities for scheduled crawling
FACILITIES = ["대강당", "중강당", "소강당", "5남소강당"]

def background_scheduler():
    """
    Background scheduler that triggers crawling for all facilities every hour.
    This function runs continuously in a separate daemon thread.
    """
    while True:
        print("[Scheduler] Starting scheduled crawling...")
        for facility in FACILITIES:
            try:
                requests.post(f"http://localhost:8000/crawl/{facility}")
            except Exception as e:
                print(f"Error crawling {facility}: {e}")
        print("[Scheduler] Crawling completed.")
        time.sleep(3600)  # Wait for 1 hour before next execution

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler to manage startup and shutdown tasks.

    Tasks:
    - Drop and recreate database tables at startup (development use only)
    - Start the background crawling scheduler
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    threading.Thread(target=background_scheduler, daemon=True).start()
    print("Background scheduler started.")

    yield
    # No shutdown tasks defined

def create_app():
    """
    Create and configure the FastAPI application instance.
    """
    app = FastAPI(lifespan=lifespan)

    # Configure CORS settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Define allowed origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(reservation_controller.router)

    # Register crawling endpoint
    @app.post("/crawl/{facility_name}")
    def crawl_facility(facility_name: str):
        """
        API endpoint to manually trigger crawling for a specific facility.

        Args:
            facility_name (str): The name of the facility to crawl.

        Returns:
            dict: Status message indicating success.
        """
        print(f"Crawling facility: {facility_name}")
        # TODO: Implement actual crawling logic and database saving here
        return {"status": "success", "facility": facility_name}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
