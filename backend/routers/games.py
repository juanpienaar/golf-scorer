"""Game management and scoring routes."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_db
from models import Game, GamePlayer, Score, Course, Hole, Player, GameStatus
from schemas import (
    GameCreate, GameOut, GameSummary, GamePlayerAdd, GamePlayerOut,
    ScoreEntry, ScoreBatchEntry, ScoreOut, LeaderboardOut
)
from services.scoring import score_game, PlayerScore, HoleInfo
from typing import List

router = APIRouter(prefix="/api/games", tags=["games"])


def _build_game_out(game: Game) -> dict:
    """Build GameOut response from a Game model."""
    return {
        "id": game.id,
        "game_code": game.game_code,
        "course_id": game.course_id,
        "course_name": game.course.name if game.course else "",
        "format": game.format,
        "status": game.status,
        "date_played": game.date_played,
        "use_handicap": game.use_handicap,
        "handicap_percentage": game.handicap_percentage,
        "num_holes": game.num_holes,
        "league_id": game.league_id,
        "notes": game.notes,
        "players": [
            {
                "id": gp.id,
                "player_id": gp.player_id,
                "player_name": gp.player.name if gp.player else "",
                "team": gp.team,
                "playing_handicap": gp.playing_handicap,
                "tee_set_id": gp.tee_set_id,
            }
            for gp in game.game_players
        ],
        "created_at": game.created_at,
    }


@router.post("/", response_model=GameOut)
async def create_game(game: GameCreate, db: AsyncSession = Depends(get_db)):
    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == game.course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    db_game = Game(
        course_id=game.course_id,
        format=game.format,
        date_played=game.date_played,
        use_handicap=game.use_handicap,
        handicap_percentage=game.handicap_percentage,
        num_holes=game.num_holes,
        league_id=game.league_id,
        created_by=game.created_by,
        notes=game.notes,
    )
    db.add(db_game)
    await db.flush()

    # Add players
    for p in game.players:
        # Look up player handicap if not provided
        playing_hcp = p.playing_handicap
        if playing_hcp is None:
            player_result = await db.execute(select(Player).where(Player.id == p.player_id))
            player = player_result.scalar_one_or_none()
            if player:
                playing_hcp = player.handicap

        gp = GamePlayer(
            game_id=db_game.id,
            player_id=p.player_id,
            team=p.team,
            playing_handicap=playing_hcp,
            tee_set_id=p.tee_set_id,
        )
        db.add(gp)

    await db.commit()

    # Reload
    result = await db.execute(
        select(Game)
        .options(
            selectinload(Game.course),
            selectinload(Game.game_players).selectinload(GamePlayer.player),
        )
        .where(Game.id == db_game.id)
    )
    return _build_game_out(result.scalar_one())


@router.get("/", response_model=List[GameSummary])
async def list_games(
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Game).options(selectinload(Game.course), selectinload(Game.game_players))
    if status:
        query = query.where(Game.status == status)
    query = query.order_by(Game.date_played.desc())
    result = await db.execute(query)
    games = result.scalars().all()
    return [
        {
            "id": g.id,
            "game_code": g.game_code,
            "course_name": g.course.name if g.course else "",
            "format": g.format,
            "status": g.status,
            "date_played": g.date_played,
            "player_count": len(g.game_players),
        }
        for g in games
    ]


@router.get("/join/{game_code}", response_model=GameOut)
async def join_game(game_code: str, db: AsyncSession = Depends(get_db)):
    """Join a game by its shareable code."""
    result = await db.execute(
        select(Game)
        .options(
            selectinload(Game.course),
            selectinload(Game.game_players).selectinload(GamePlayer.player),
        )
        .where(Game.game_code == game_code.upper())
    )
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return _build_game_out(game)


@router.get("/{game_id}", response_model=GameOut)
async def get_game(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Game)
        .options(
            selectinload(Game.course),
            selectinload(Game.game_players).selectinload(GamePlayer.player),
        )
        .where(Game.id == game_id)
    )
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return _build_game_out(game)


@router.post("/{game_id}/players", response_model=GamePlayerOut)
async def add_player_to_game(
    game_id: str, player: GamePlayerAdd, db: AsyncSession = Depends(get_db)
):
    # Verify game exists
    game_result = await db.execute(select(Game).where(Game.id == game_id))
    game = game_result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get player info
    player_result = await db.execute(select(Player).where(Player.id == player.player_id))
    db_player = player_result.scalar_one_or_none()
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found")

    playing_hcp = player.playing_handicap if player.playing_handicap is not None else db_player.handicap

    gp = GamePlayer(
        game_id=game_id,
        player_id=player.player_id,
        team=player.team,
        playing_handicap=playing_hcp,
        tee_set_id=player.tee_set_id,
    )
    db.add(gp)
    await db.commit()
    await db.refresh(gp)

    return {
        "id": gp.id,
        "player_id": gp.player_id,
        "player_name": db_player.name,
        "team": gp.team,
        "playing_handicap": gp.playing_handicap,
        "tee_set_id": gp.tee_set_id,
    }


@router.post("/{game_id}/start")
async def start_game(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    game.status = GameStatus.IN_PROGRESS
    await db.commit()
    return {"ok": True, "status": "in_progress"}


@router.post("/{game_id}/complete")
async def complete_game(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    game.status = GameStatus.COMPLETED
    await db.commit()
    return {"ok": True, "status": "completed"}


# ─── Scoring ──────────────────────────────────────────────────────

@router.post("/{game_id}/scores")
async def submit_score(
    game_id: str, entry: ScoreEntry, db: AsyncSession = Depends(get_db)
):
    """Submit or update a single hole score."""
    # Check if score exists
    result = await db.execute(
        select(Score).where(
            Score.game_id == game_id,
            Score.player_id == entry.player_id,
            Score.hole_number == entry.hole_number,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.strokes = entry.strokes
        existing.putts = entry.putts
        existing.fairway_hit = entry.fairway_hit
        existing.gir = entry.gir
        existing.penalties = entry.penalties
        existing.recorded_at = datetime.utcnow()
    else:
        score = Score(
            game_id=game_id,
            player_id=entry.player_id,
            hole_number=entry.hole_number,
            strokes=entry.strokes,
            putts=entry.putts,
            fairway_hit=entry.fairway_hit,
            gir=entry.gir,
            penalties=entry.penalties,
        )
        db.add(score)

    # Auto-start game if still in setup
    game_result = await db.execute(select(Game).where(Game.id == game_id))
    game = game_result.scalar_one_or_none()
    if game and game.status == GameStatus.SETUP:
        game.status = GameStatus.IN_PROGRESS

    await db.commit()
    return {"ok": True}


@router.post("/{game_id}/scores/batch")
async def submit_scores_batch(
    game_id: str, batch: ScoreBatchEntry, db: AsyncSession = Depends(get_db)
):
    """Submit multiple scores at once."""
    for entry in batch.scores:
        result = await db.execute(
            select(Score).where(
                Score.game_id == game_id,
                Score.player_id == entry.player_id,
                Score.hole_number == entry.hole_number,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.strokes = entry.strokes
            existing.putts = entry.putts
            existing.fairway_hit = entry.fairway_hit
            existing.gir = entry.gir
            existing.penalties = entry.penalties
        else:
            score = Score(
                game_id=game_id,
                player_id=entry.player_id,
                hole_number=entry.hole_number,
                strokes=entry.strokes,
                putts=entry.putts,
                fairway_hit=entry.fairway_hit,
                gir=entry.gir,
                penalties=entry.penalties,
            )
            db.add(score)

    await db.commit()
    return {"ok": True, "count": len(batch.scores)}


@router.get("/{game_id}/scores", response_model=List[ScoreOut])
async def get_scores(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Score).where(Score.game_id == game_id).order_by(Score.player_id, Score.hole_number)
    )
    return result.scalars().all()


# ─── Leaderboard ──────────────────────────────────────────────────

@router.get("/{game_id}/leaderboard")
async def get_leaderboard(game_id: str, db: AsyncSession = Depends(get_db)):
    """Get live leaderboard for a game, computed using the scoring engine."""
    # Load game with all relationships
    result = await db.execute(
        select(Game)
        .options(
            selectinload(Game.course).selectinload(Course.holes),
            selectinload(Game.game_players).selectinload(GamePlayer.player),
            selectinload(Game.scores),
        )
        .where(Game.id == game_id)
    )
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Build hole info
    holes = [
        HoleInfo(
            hole_number=h.hole_number,
            par=h.par,
            stroke_index=h.stroke_index,
            yards=h.yards,
        )
        for h in sorted(game.course.holes, key=lambda h: h.hole_number)
    ]

    # Build player scores
    player_scores = []
    for gp in game.game_players:
        ps = PlayerScore(
            player_id=gp.player_id,
            player_name=gp.player.name,
            team=gp.team,
            playing_handicap=gp.playing_handicap or 0,
        )
        for score in game.scores:
            if score.player_id == gp.player_id and score.strokes is not None:
                ps.hole_scores[score.hole_number] = score.strokes
        player_scores.append(ps)

    # Score the game
    results = score_game(game.format.value, player_scores, holes, game.use_handicap)

    return {
        "game_id": game.id,
        "game_code": game.game_code,
        "course_name": game.course.name,
        "format": game.format,
        "status": game.status,
        "results": results,
        "last_updated": datetime.utcnow().isoformat(),
    }


@router.get("/code/{game_code}/leaderboard")
async def get_leaderboard_by_code(game_code: str, db: AsyncSession = Depends(get_db)):
    """Get leaderboard by game code (for shared links)."""
    result = await db.execute(
        select(Game).where(Game.game_code == game_code.upper())
    )
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return await get_leaderboard(game.id, db)
