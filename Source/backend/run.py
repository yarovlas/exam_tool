import os

import uvicorn


if __name__ == "__main__":
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    reload_enabled = os.getenv("APP_RELOAD", "true").lower() == "true"

    uvicorn.run("app.main:app", host=host, port=port, reload=reload_enabled)
