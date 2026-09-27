from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.schemas import AssetOut, ChatRequest, ChatResponse, HealthResponse, SessionResponse
from app.container import Container, get_container

router = APIRouter()
ContainerDep = Annotated[Container, Depends(get_container)]


@router.get("/health", response_model=HealthResponse)
def health(container: ContainerDep) -> HealthResponse:
    return HealthResponse(status="ok", extractor=container.chat_service.extractor_name)


@router.post("/api/v1/sessions", response_model=SessionResponse, status_code=201)
def create_session(container: ContainerDep) -> SessionResponse:
    state = container.chat_service.create_session()
    return SessionResponse.model_validate(state.model_dump())


@router.get("/api/v1/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, container: ContainerDep) -> SessionResponse:
    state = container.chat_service.get_session(session_id)
    return SessionResponse.model_validate(state.model_dump())


@router.post("/api/v1/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, container: ContainerDep) -> ChatResponse:
    result = container.chat_service.chat(payload.message, payload.session_id)
    assets = [
        AssetOut(
            id=asset.asset_id,
            description=asset.description,
            url=router.url_path_for("asset_image", asset_id=asset.asset_id),
        )
        for asset in result.assets
    ]
    return ChatResponse.model_validate(result.model_dump(exclude={"assets"}) | {"assets": assets})


@router.get("/api/v1/assets/{asset_id}/image", name="asset_image")
def asset_image(asset_id: str, container: ContainerDep) -> FileResponse:
    asset = container.asset_repository.get(asset_id)
    if asset is None or not asset.file.is_file():
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' was not found")
    return FileResponse(asset.file)
