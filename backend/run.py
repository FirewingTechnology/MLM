import uvicorn

if __name__ == "__main__":
    print("Starting Virtual Binary MLM FastAPI Server on http://127.0.0.1:5000 (DEMO MODE)...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )
