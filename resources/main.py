from fastapi import FastAPI
import json


app = FastAPI()


# Custom OpenAPI 3.0 specification file
def custom_openapi():
    with open('openapi.json', 'r') as file:
        app.openapi_schema = json.load(file)
        return app.openapi_schema


app.openapi = custom_openapi


# Endpoints
@app.get("/board")
async def root():
    return [
        {"name": "round"},
        {"name": "score"},
        {"name": "map"},
        {"name": "nwo"}
    ]
