import os
import uvicorn
import openai

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7070))
    is_dev = os.environ.get("ENV", "development") == "development"
    print(f"Starting Virtual Binary MLM FastAPI Server on port {port} (DEMO MODE)...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=is_dev
    )
