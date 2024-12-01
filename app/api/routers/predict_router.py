from fastapi import APIRouter, Depends

from app.api.models.predict import PredictIn, PredictOut
from app.container import Container
from app.workers.model_client import ModelClient

router = APIRouter(tags=["predict"])


@router.post("/predict")
def predict(data: PredictIn, model: ModelClient = Depends(Container.model_client)) -> PredictOut:
    return model.router_inference(data.model_dump())
