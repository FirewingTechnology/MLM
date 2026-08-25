import uvicorn

if __name__ == "__main__":
    print("Starting Virtual Binary MLM FastAPI Server on https://mlm-lkod.onrender.com (DEMO MODE)...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=7070,
        reload=True
    )
