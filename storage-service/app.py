from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Storage Service")


class Storage(BaseModel):
    storage_id: int
    location: str
    status: str


class StorageRequest(BaseModel):
    storage_id: int


# Temporary in-memory storage
storage_data = [
    Storage(storage_id=1, location="A-01", status="AVAILABLE"),
    Storage(storage_id=2, location="A-02", status="AVAILABLE"),
    Storage(storage_id=3, location="B-01", status="AVAILABLE")
]


@app.get("/")
def home():
    return {
        "service": "Storage Service",
        "status": "running"
    }


@app.post("/storage")
def create_storage(storage: Storage):
    for item in storage_data:
        if item.storage_id == storage.storage_id:
            raise HTTPException(
                status_code=400,
                detail="Storage ID already exists"
            )

    storage_data.append(storage)

    return {
        "message": "Storage created successfully",
        "storage": storage
    }


@app.get("/storage")
def get_storage():
    return storage_data


@app.get("/storage/available")
def get_available_storage():
    return [
        storage
        for storage in storage_data
        if storage.status == "AVAILABLE"
    ]


@app.post("/storage/assign")
def assign_storage(request: StorageRequest):
    for storage in storage_data:
        if storage.storage_id == request.storage_id:

            if storage.status == "ASSIGNED":
                raise HTTPException(
                    status_code=400,
                    detail="Storage is already assigned"
                )

            storage.status = "ASSIGNED"

            return {
                "message": "Storage assigned successfully",
                "storage": storage
            }

    raise HTTPException(
        status_code=404,
        detail="Storage not found"
    )


@app.post("/storage/release")
def release_storage(request: StorageRequest):
    for storage in storage_data:
        if storage.storage_id == request.storage_id:

            storage.status = "AVAILABLE"

            return {
                "message": "Storage released successfully",
                "storage": storage
            }

    raise HTTPException(
        status_code=404,
        detail="Storage not found"
    )