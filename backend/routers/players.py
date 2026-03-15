"""Player management routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Player
from schemas import PlayerCreate, PlayerUpdate, PlayerOut, PlayerLogin
from typing import List

router = APIRouter(prefix="/api/players", tags=["players"])


@router.post("/", response_model=PlayerOut)
async def create_player(player: PlayerCreate, db: AsyncSession = Depends(get_db)):
    db_player = Player(**player.model_dump())
    db.add(db_player)
    await db.commit()
    await db.refresh(db_player)
    return db_player


@router.post("/login")
async def login_player(login: PlayerLogin, db: AsyncSession = Depends(get_db)):
    """Simple login by name + optional PIN."""
    query = select(Player).where(Player.name == login.name)
    result = await db.execute(query)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    if player.pin and player.pin != login.pin:
        raise HTTPException(status_code=401, detail="Invalid PIN")

    return {"id": player.id, "name": player.name, "handicap": player.handicap}


@router.get("/", response_model=List[PlayerOut])
async def list_players(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).order_by(Player.name))
    return result.scalars().all()


@router.get("/{player_id}", response_model=PlayerOut)
async def get_player(player_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.patch("/{player_id}", response_model=PlayerOut)
async def update_player(
    player_id: str, update: PlayerUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(player, field, value)

    await db.commit()
    await db.refresh(player)
    return player


@router.delete("/{player_id}")
async def delete_player(player_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    await db.delete(player)
    await db.commit()
    return {"ok": True}
