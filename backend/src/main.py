from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controllers import router
import os

# Get frontend origin from env
frontend_origin = "*" # os.getenv("FRONTEND_ORIGIN", "*")
# is_dev = os.getenv("ENV", "dev") == "dev"

def create_app():
    """Creates and configures the FastAPI application."""
    app = FastAPI(
        # docs_url=None, # deploy setting
        # redoc_url=None
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

    return app

# Create the FastAPI application
app = create_app()

if __name__ == "__main__":
    import uvicorn
    # Running without --reload for testing purposes
    uvicorn.run("main:app", host="0.0.0.0", port=8000)  # Run without --reload
