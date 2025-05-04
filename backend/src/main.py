from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from controllers import reservation_controller
from services.crawling_service import crawl_facility_reservations

import traceback

# List of facility names for periodic crawling
FACILITIES = ["대강당", "중강당", "소강당", "5남소강당"]

# Background scheduler instance
scheduler = BackgroundScheduler()


def scheduled_crawling():
    """Performs scheduled crawling for all defined facilities.

    This function is called automatically at fixed intervals by the APScheduler.
    It crawls each facility and handles exceptions gracefully.
    """
    print("[Scheduler] Starting scheduled crawling...")
    for facility in FACILITIES:
        try:
            crawl_facility_reservations(None, facility)
        except Exception as e:
            print(f"[Scheduler Error] Failed to crawl {facility}: {e}")
            traceback.print_exc()
    print("[Scheduler] Crawling completed.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the startup and shutdown lifecycle of the FastAPI app.

    Args:
        app: The FastAPI application instance.

    This function starts the background scheduler at startup and
    ensures a clean shutdown at termination.
    """
    scheduler.add_job(scheduled_crawling, "interval", minutes=10)
    scheduler.start()
    print("[Startup] Background scheduler started.")
    yield
    print("[Shutdown] Background scheduler stopping...")
    scheduler.shutdown()


def create_app():
    """Creates and configures the FastAPI application.

    Returns:
        A FastAPI app instance with CORS enabled and routing registered.
    """
    app = FastAPI(lifespan=lifespan)

    # Enable CORS for all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register application routers
    app.include_router(reservation_controller.router)

    @app.post("/crawl/{facility_name}")
    def crawl_facility(facility_name: str):
        """Manually triggers crawling for a specific facility.

        Args:
            facility_name: The name of the facility to crawl.

        Returns:
            A dictionary containing the crawling result or error details.
        """
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

    # Start the application with hot-reload
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
