"""League and Order of Merit routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from database import get_db
from models import (
    League, LeagueMember, Player, Game, GamePlayer, Score, Hole, Course, GameStatus
)
from schemas import (
    LeagueCreate, LeagueOut, LeagueMemberOut, OrderOfMeritOut, OrderOfMeritEntry
)
from services.scoring import (
    score_stableford, PlayerScore, HoleInfo, get_handicap_strokes_per_hole,
    calculate_stableford_points
)
from typing import List

router = APIRouter(prefix="/api/leagues", tags=["leagues"])


@router.post("/", response_model=LeagueOut)
async def create_league(league: LeagueCreate, db: AsyncSession = Depends(get_db)):
    db_league = League(**league.model_dump())
    db.add(db_league)
    await db.commit()
    await db.refresh(db_league)
    return {**db_league.__dict__, "member_count": 0}


@router.get("/", response_model=List[LeagueOut])
async def list_leagues(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(League).options(selectinload(League.members)).order_by(League.year.desc(), League.name)
    )
    leagues = result.scalars().all()
    return [
        {**l.__dict__, "member_count": len(l.members)}
        for l in leagues
    ]


@router.get("/{league_id}", response_model=LeagueOut)
async def get_league(league_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(League).options(selectinload(League.members)).where(League.id == league_id)
    )
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return {**league.__dict__, "member_count": len(league.members)}


@router.post("/{league_id}/members")
async def add_member(league_id: str, player_id: str, db: AsyncSession = Depends(get_db)):
    # Verify league and player exist
    league = (await db.execute(select(League).where(League.id == league_id))).scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    player = (await db.execute(select(Player).where(Player.id == player_id))).scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Check not already a member
    existing = (await db.execute(
        select(LeagueMember).where(
            LeagueMember.league_id == league_id,
            LeagueMember.player_id == player_id,
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Already a member")

    member = LeagueMember(league_id=league_id, player_id=player_id)
    db.add(member)
    await db.commit()
    return {"ok": True}


@router.get("/{league_id}/members", response_model=List[LeagueMemberOut])
async def list_members(league_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LeagueMember)
        .options(selectinload(LeagueMember.player))
        .where(LeagueMember.league_id == league_id)
    )
    members = result.scalars().all()
    return [
        {
            "player_id": m.player_id,
            "player_name": m.player.name,
            "handicap": m.player.handicap,
            "joined_at": m.joined_at,
        }
        for m in members
    ]


@router.delete("/{league_id}/members/{player_id}")
async def remove_member(league_id: str, player_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LeagueMember).where(
            LeagueMember.league_id == league_id,
            LeagueMember.player_id == player_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    await db.delete(member)
    await db.commit()
    return {"ok": True}


@router.get("/{league_id}/order-of-merit")
async def get_order_of_merit(league_id: str, db: AsyncSession = Depends(get_db)):
    """
    Calculate Order of Merit for a league.
    Rules:
    - Only completed games linked to this league count
    - Another league member must have played in the same game (attestor)
    - Scores are calculated as stableford points (handicap-adjusted)
    - Best N (league.best_of) scores count
    - Ranked by total of best scores
    """
    # Load league
    league_result = await db.execute(
        select(League).options(selectinload(League.members)).where(League.id == league_id)
    )
    league = league_result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    member_ids = {m.player_id for m in league.members}

    # Load all completed games for this league
    games_result = await db.execute(
        select(Game)
        .options(
            selectinload(Game.course).selectinload(Course.holes),
            selectinload(Game.game_players).selectinload(GamePlayer.player),
            selectinload(Game.scores),
        )
        .where(Game.league_id == league_id, Game.status == GameStatus.COMPLETED)
    )
    games = games_result.scalars().all()

    # Calculate stableford scores per player per game
    player_scores: dict = {}  # player_id -> list of (date, stableford_total, course_name)

    for game in games:
        # Check which league members played
        game_member_ids = {
            gp.player_id for gp in game.game_players if gp.player_id in member_ids
        }

        # Need at least min_attestors other members in the game
        holes = sorted(game.course.holes, key=lambda h: h.hole_number)
        hole_infos = [
            HoleInfo(h.hole_number, h.par, h.stroke_index, h.yards)
            for h in holes
        ]

        for gp in game.game_players:
            if gp.player_id not in member_ids:
                continue

            # Check attestor requirement: at least min_attestors OTHER members played
            other_members = game_member_ids - {gp.player_id}
            if len(other_members) < league.min_attestors:
                continue

            # Calculate stableford score for this player in this game
            playing_hcp = gp.playing_handicap or 0
            hcp_strokes = get_handicap_strokes_per_hole(round(playing_hcp), hole_infos)

            total_points = 0
            holes_scored = 0
            for score in game.scores:
                if score.player_id == gp.player_id and score.strokes is not None:
                    hole_info = next(
                        (h for h in hole_infos if h.hole_number == score.hole_number), None
                    )
                    if hole_info:
                        points = calculate_stableford_points(
                            score.strokes, hole_info.par, hcp_strokes[score.hole_number]
                        )
                        total_points += points
                        holes_scored += 1

            # Only count full rounds
            if holes_scored >= game.num_holes:
                if gp.player_id not in player_scores:
                    player_scores[gp.player_id] = []
                player_scores[gp.player_id].append({
                    "date": game.date_played.isoformat(),
                    "points": total_points,
                    "course": game.course.name,
                    "game_id": game.id,
                })

    # Build Order of Merit
    entries = []
    for member in league.members:
        scores = player_scores.get(member.player_id, [])
        # Sort by points descending, take best N
        scores.sort(key=lambda s: -s["points"])
        best = scores[:league.best_of]
        best_points = [s["points"] for s in best]
        total = sum(best_points)
        avg = total / len(best_points) if best_points else 0

        entries.append({
            "player_id": member.player_id,
            "player_name": member.player.name,
            "handicap": member.player.handicap,
            "qualifying_rounds": len(scores),
            "best_scores": best_points,
            "total_points": total,
            "average_points": round(avg, 1),
            "all_scores": scores,
        })

    # Sort by total points descending
    entries.sort(key=lambda e: (-e["total_points"], -e["average_points"]))

    # Add ranks
    for i, entry in enumerate(entries):
        entry["rank"] = i + 1

    return {
        "league_id": league.id,
        "league_name": league.name,
        "year": league.year,
        "best_of": league.best_of,
        "entries": entries,
    }
