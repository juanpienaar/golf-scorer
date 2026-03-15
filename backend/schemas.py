"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from models import GameFormat, GameStatus


# ─── Player ───────────────────────────────────────────────────────
class PlayerCreate(BaseModel):
    name: str
    pin: Optional[str] = None
    handicap: float = 0.0
    email: Optional[str] = None

class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    pin: Optional[str] = None
    handicap: Optional[float] = None
    email: Optional[str] = None

class PlayerOut(BaseModel):
    id: str
    name: str
    handicap: float
    email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PlayerLogin(BaseModel):
    name: str
    pin: Optional[str] = None


# ─── Course / Holes ──────────────────────────────────────────────
class HoleOut(BaseModel):
    hole_number: int
    par: int
    stroke_index: int
    yards: Optional[int] = None

    class Config:
        from_attributes = True

class TeeHoleOut(BaseModel):
    hole_number: int
    yards: int

    class Config:
        from_attributes = True

class TeeSetOut(BaseModel):
    id: str
    name: str
    color: Optional[str] = None
    course_rating: Optional[float] = None
    slope_rating: Optional[int] = None
    total_yards: Optional[int] = None
    tee_holes: List[TeeHoleOut] = []

    class Config:
        from_attributes = True

class CourseOut(BaseModel):
    id: str
    name: str
    location: Optional[str] = None
    country: Optional[str] = None
    num_holes: int
    course_rating: Optional[float] = None
    slope_rating: Optional[int] = None
    holes: List[HoleOut] = []
    tee_sets: List[TeeSetOut] = []

    class Config:
        from_attributes = True

class CourseCreate(BaseModel):
    name: str
    location: Optional[str] = None
    country: Optional[str] = None
    num_holes: int = 18
    course_rating: Optional[float] = None
    slope_rating: Optional[int] = None
    holes: List[HoleOut] = []

class CourseSummary(BaseModel):
    id: str
    name: str
    location: Optional[str] = None
    num_holes: int

    class Config:
        from_attributes = True


# ─── Game ─────────────────────────────────────────────────────────
class GamePlayerAdd(BaseModel):
    player_id: str
    team: Optional[str] = None
    playing_handicap: Optional[float] = None
    tee_set_id: Optional[str] = None

class GamePlayerOut(BaseModel):
    id: str
    player_id: str
    player_name: str
    team: Optional[str] = None
    playing_handicap: Optional[float] = None
    tee_set_id: Optional[str] = None

    class Config:
        from_attributes = True

class GameCreate(BaseModel):
    course_id: str
    format: GameFormat
    date_played: Optional[date] = None
    use_handicap: bool = True
    handicap_percentage: int = 100
    num_holes: int = 18
    league_id: Optional[str] = None
    created_by: Optional[str] = None
    notes: Optional[str] = None
    players: List[GamePlayerAdd] = []

class GameOut(BaseModel):
    id: str
    game_code: str
    course_id: str
    course_name: str
    format: GameFormat
    status: GameStatus
    date_played: date
    use_handicap: bool
    handicap_percentage: int
    num_holes: int
    league_id: Optional[str] = None
    notes: Optional[str] = None
    players: List[GamePlayerOut] = []
    created_at: datetime

    class Config:
        from_attributes = True

class GameSummary(BaseModel):
    id: str
    game_code: str
    course_name: str
    format: GameFormat
    status: GameStatus
    date_played: date
    player_count: int

    class Config:
        from_attributes = True


# ─── Scores ───────────────────────────────────────────────────────
class ScoreEntry(BaseModel):
    player_id: str
    hole_number: int
    strokes: int
    putts: Optional[int] = None
    fairway_hit: Optional[bool] = None
    gir: Optional[bool] = None
    penalties: int = 0

class ScoreBatchEntry(BaseModel):
    scores: List[ScoreEntry]

class ScoreOut(BaseModel):
    player_id: str
    hole_number: int
    strokes: Optional[int] = None
    putts: Optional[int] = None
    fairway_hit: Optional[bool] = None
    gir: Optional[bool] = None
    penalties: int = 0

    class Config:
        from_attributes = True


# ─── Leaderboard ──────────────────────────────────────────────────
class HoleScore(BaseModel):
    hole_number: int
    par: int
    stroke_index: int
    strokes: Optional[int] = None
    net_strokes: Optional[int] = None
    stableford_points: Optional[int] = None
    to_par: Optional[int] = None

class PlayerLeaderboardEntry(BaseModel):
    player_id: str
    player_name: str
    team: Optional[str] = None
    playing_handicap: Optional[float] = None
    holes_played: int
    gross_total: Optional[int] = None
    net_total: Optional[int] = None
    total_stableford: Optional[int] = None
    to_par: Optional[int] = None
    thru: int  # Current hole
    hole_scores: List[HoleScore] = []

class TeamLeaderboardEntry(BaseModel):
    team: str
    players: List[str]
    team_score: Optional[int] = None
    team_stableford: Optional[int] = None
    team_to_par: Optional[int] = None

class LeaderboardOut(BaseModel):
    game_id: str
    game_code: str
    course_name: str
    format: GameFormat
    status: GameStatus
    individual: List[PlayerLeaderboardEntry] = []
    teams: List[TeamLeaderboardEntry] = []
    last_updated: datetime


# ─── League / Order of Merit ─────────────────────────────────────
class LeagueCreate(BaseModel):
    name: str
    year: int
    best_of: int = 15
    min_attestors: int = 1
    scoring_type: str = "stableford"

class LeagueOut(BaseModel):
    id: str
    name: str
    year: int
    best_of: int
    min_attestors: int
    scoring_type: str
    member_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

class LeagueMemberOut(BaseModel):
    player_id: str
    player_name: str
    handicap: float
    joined_at: datetime

    class Config:
        from_attributes = True

class OrderOfMeritEntry(BaseModel):
    rank: int
    player_id: str
    player_name: str
    handicap: float
    qualifying_rounds: int
    best_scores: List[int]  # Best N stableford scores
    total_points: int
    average_points: float

class OrderOfMeritOut(BaseModel):
    league_id: str
    league_name: str
    year: int
    best_of: int
    entries: List[OrderOfMeritEntry]


# ─── Format-specific results ─────────────────────────────────────
class WolfieHoleResult(BaseModel):
    hole_number: int
    wolf: str  # Player name
    wolf_partner: Optional[str] = None
    lone_wolf: bool = False
    hole_winner: Optional[str] = None
    points: dict  # player_name -> points

class SkinResult(BaseModel):
    hole_number: int
    winner: Optional[str] = None
    carry_over: bool = False
    value: int = 1

class FormatResult(BaseModel):
    """Generic container for format-specific results."""
    format: GameFormat
    data: dict  # Format-specific data
