import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/dummy")
def dummy_endpoint():
    return {"message": "Dummy endpoint"}

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=6000, reload=True)