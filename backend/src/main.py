from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from controllers import router
from services import crawl_facility_reservations
import traceback
import os

# List of facility names for periodic crawling
FACILITIES = ["대강당", "중강당", "소강당", "5남소강당"]

# Get frontend origin from env
frontend_origin = os.getenv("FRONTEND_ORIGIN", "*")
# is_dev = os.getenv("ENV", "dev") == "dev"

# Background scheduler instanceconfig_loader
scheduler = BackgroundScheduler()

def scheduled_crawling():
    """Performs scheduled crawling for all defined facilities."""
    print("[Scheduler] Starting scheduled crawling...")
    for facility in FACILITIES:
        try:
            print(f"[Scheduler] Crawling facility: {facility}")
            crawl_facility_reservations(None, facility)
        except Exception as e:
            print(f"[Scheduler Error] Failed to crawl {facility}: {e}")
            traceback.print_exc()
    print("[Scheduler] Crawling completed.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the startup and shutdown lifecycle of the FastAPI app."""
    print("[Startup] Running first crawl manually...")
    # scheduled_crawling()  # Trigger first crawl immediately

    # 🕘 Only allow crawling from 09:00 to 17:30 (inclusive), every 30 min
    trigger = CronTrigger(minute='0,30', hour='9-17')
    scheduler.add_job(scheduled_crawling, trigger)
    scheduler.start()
    print("[Startup] Background scheduler started.")
    
    yield
    
    print("[Shutdown] Background scheduler stopping...")
    scheduler.shutdown()

def create_app():
    """Creates and configures the FastAPI application."""
    app = FastAPI(
        lifespan=lifespan,
        docs_url=None, # deploy setting
        redoc_url=None
    )
    # Enable CORS for all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register application routers
    app.include_router(router)

    @app.post("/crawl/{facility_name}")
    def crawl_facility(facility_name: str):
        """Manually triggers crawling for a specific facility."""
        print(f"[Manual Trigger] Crawling facility: {facility_name}")
        try:
            result = crawl_facility_reservations(None, facility_name)
            return result
        except Exception as e:
            print(f"[Manual Error] Failed to crawl {facility_name}: {e}")
            traceback.print_exc()
            return {"status": "error", "reason": str(e)}

    return app

# Create the FastAPI application
app = create_app()

if __name__ == "__main__":
    import uvicorn
    # Running without --reload for testing purposes
    uvicorn.run("main:app", host="0.0.0.0", port=8000)  # Run without --reload
