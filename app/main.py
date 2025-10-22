from fastapi import FastAPI

app = FastAPI(title="Business management system API")

@app.get("/")
def read_root():
    return {"message": "Hello from business management system!"}
