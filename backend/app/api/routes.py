from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.schemas import (
    AssetOut,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    MessageOut,
    SessionResponse,
)
from app.container import Container, get_container
from app.domain.models.asset import Asset
from app.domain.models.conversation import ConversationState

router = APIRouter()
ContainerDep = Annotated[Container, Depends(get_container)]


def _asset_out(asset: Asset) -> AssetOut:
    return AssetOut(
        id=asset.asset_id,
        description=asset.description,
        url=router.url_path_for("asset_image", asset_id=asset.asset_id),
    )


def _session_out(state: ConversationState, container: Container) -> SessionResponse:
    def assets(ids: list[str]) -> list[AssetOut]:
        found = (container.asset_repository.get(asset_id) for asset_id in ids)
        return [_asset_out(asset) for asset in found if asset is not None]

    messages = [
        MessageOut(
            role=message.role,
            content=message.content,
            assets=assets(message.asset_ids),
            created_at=message.created_at,
        )
        for message in state.message_history
    ]
    return SessionResponse.model_validate(
        state.model_dump(exclude={"message_history"})
        | {"message_history": messages, "missing_slots": state.last_asked_fields}
    )


@router.get("/health", response_model=HealthResponse)
def health(container: ContainerDep) -> HealthResponse:
    return HealthResponse(status="ok", extractor=container.chat_service.extractor_name)


@router.post("/api/v1/sessions", response_model=SessionResponse, status_code=201)
def create_session(container: ContainerDep) -> SessionResponse:
    return _session_out(container.chat_service.create_session(), container)


@router.get("/api/v1/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, container: ContainerDep) -> SessionResponse:
    return _session_out(container.chat_service.get_session(session_id), container)


@router.post("/api/v1/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, container: ContainerDep) -> ChatResponse:
    result = container.chat_service.chat(payload.message, payload.session_id)
    assets = [_asset_out(asset) for asset in result.assets]
    return ChatResponse.model_validate(result.model_dump(exclude={"assets"}) | {"assets": assets})


@router.get("/api/v1/assets/{asset_id}/image", name="asset_image")
def asset_image(asset_id: str, container: ContainerDep) -> FileResponse:
    asset = container.asset_repository.get(asset_id)
    if asset is None or not asset.file.is_file():
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' was not found")
    return FileResponse(asset.file)
