from fastapi import APIRouter

router = APIRouter()

@router.get("/simple")
def simple_test():
    return {"message": "Simple test working"}
