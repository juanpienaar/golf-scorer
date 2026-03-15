"""SQLAlchemy database models."""
import uuid
import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Enum, JSON, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


def generate_uuid():
    return str(uuid.uuid4())


def generate_game_code():
    """Generate a short shareable game code."""
    return uuid.uuid4().hex[:8].upper()


class GameFormat(str, enum.Enum):
    STROKEPLAY = "strokeplay"
    STABLEFORD = "stableford"
    BETTER_BALL_FOURBALL = "better_ball_fourball"
    BETTER_BALL_STABLEFORD = "better_ball_stableford"
    FOURSOMES = "foursomes"
    COMBINED_TEAM_STABLEFORD = "combined_team_stableford"
    WOLFIE = "wolfie"
    PERCH = "perch"
    SKINS = "skins"
    MATCH_PLAY = "match_play"
    TEXAS_SCRAMBLE = "texas_scramble"
    GREENSOMES = "greensomes"
    CHAPMAN = "chapman"
    AMBROSE = "ambrose"
    FLAGS = "flags"


class GameStatus(str, enum.Enum):
    SETUP = "setup"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Player(Base):
    __tablename__ = "players"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    pin = Column(String(6), nullable=True)  # Optional simple PIN
    handicap = Column(Float, default=0.0)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    game_players = relationship("GamePlayer", back_populates="player")
    scores = relationship("Score", back_populates="player")
    league_memberships = relationship("LeagueMember", back_populates="player")


class Course(Base):
    __tablename__ = "courses"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    location = Column(String(200), nullable=True)
    country = Column(String(100), nullable=True)
    num_holes = Column(Integer, default=18)
    course_rating = Column(Float, nullable=True)
    slope_rating = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    holes = relationship("Hole", back_populates="course", order_by="Hole.hole_number")
    tee_sets = relationship("TeeSet", back_populates="course")
    games = relationship("Game", back_populates="course")


class TeeSet(Base):
    """Different tee options for a course (e.g., white, yellow, red)."""
    __tablename__ = "tee_sets"

    id = Column(String, primary_key=True, default=generate_uuid)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    name = Column(String(50), nullable=False)  # e.g., "White", "Yellow", "Red"
    color = Column(String(20), nullable=True)
    course_rating = Column(Float, nullable=True)
    slope_rating = Column(Integer, nullable=True)
    total_yards = Column(Integer, nullable=True)

    course = relationship("Course", back_populates="tee_sets")
    tee_holes = relationship("TeeHole", back_populates="tee_set")


class TeeHole(Base):
    """Yardage for each hole from a specific tee set."""
    __tablename__ = "tee_holes"

    id = Column(String, primary_key=True, default=generate_uuid)
    tee_set_id = Column(String, ForeignKey("tee_sets.id"), nullable=False)
    hole_number = Column(Integer, nullable=False)
    yards = Column(Integer, nullable=False)

    tee_set = relationship("TeeSet", back_populates="tee_holes")

    __table_args__ = (
        UniqueConstraint("tee_set_id", "hole_number", name="uq_tee_hole"),
    )


class Hole(Base):
    __tablename__ = "holes"

    id = Column(String, primary_key=True, default=generate_uuid)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    hole_number = Column(Integer, nullable=False)
    par = Column(Integer, nullable=False)
    stroke_index = Column(Integer, nullable=False)  # Handicap stroke index
    yards = Column(Integer, nullable=True)  # Default/primary yardage

    course = relationship("Course", back_populates="holes")

    __table_args__ = (
        UniqueConstraint("course_id", "hole_number", name="uq_course_hole"),
    )


class Game(Base):
    __tablename__ = "games"

    id = Column(String, primary_key=True, default=generate_uuid)
    game_code = Column(String(8), unique=True, default=generate_game_code)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    format = Column(Enum(GameFormat), nullable=False)
    status = Column(Enum(GameStatus), default=GameStatus.SETUP)
    date_played = Column(Date, default=date.today)
    use_handicap = Column(Boolean, default=True)
    handicap_percentage = Column(Integer, default=100)  # % of handicap to apply
    num_holes = Column(Integer, default=18)  # 9 or 18
    league_id = Column(String, ForeignKey("leagues.id"), nullable=True)
    created_by = Column(String, ForeignKey("players.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course = relationship("Course", back_populates="games")
    game_players = relationship("GamePlayer", back_populates="game")
    scores = relationship("Score", back_populates="game")
    league = relationship("League", back_populates="games")


class GamePlayer(Base):
    __tablename__ = "game_players"

    id = Column(String, primary_key=True, default=generate_uuid)
    game_id = Column(String, ForeignKey("games.id"), nullable=False)
    player_id = Column(String, ForeignKey("players.id"), nullable=False)
    team = Column(String(50), nullable=True)  # Team name/identifier for team games
    playing_handicap = Column(Float, nullable=True)  # Handicap at time of game
    tee_set_id = Column(String, ForeignKey("tee_sets.id"), nullable=True)

    game = relationship("Game", back_populates="game_players")
    player = relationship("Player", back_populates="game_players")
    tee_set = relationship("TeeSet")

    __table_args__ = (
        UniqueConstraint("game_id", "player_id", name="uq_game_player"),
    )


class Score(Base):
    __tablename__ = "scores"

    id = Column(String, primary_key=True, default=generate_uuid)
    game_id = Column(String, ForeignKey("games.id"), nullable=False)
    player_id = Column(String, ForeignKey("players.id"), nullable=False)
    hole_number = Column(Integer, nullable=False)
    strokes = Column(Integer, nullable=True)  # Null = not yet scored
    putts = Column(Integer, nullable=True)
    fairway_hit = Column(Boolean, nullable=True)
    gir = Column(Boolean, nullable=True)  # Green in regulation
    penalties = Column(Integer, default=0)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="scores")
    player = relationship("Player", back_populates="scores")

    __table_args__ = (
        UniqueConstraint("game_id", "player_id", "hole_number", name="uq_score"),
    )


class League(Base):
    __tablename__ = "leagues"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    year = Column(Integer, nullable=False)
    best_of = Column(Integer, default=15)  # Best N scores count
    min_attestors = Column(Integer, default=1)  # Min league members in same game
    scoring_type = Column(String(50), default="stableford")  # How OOM scores are calculated
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("LeagueMember", back_populates="league")
    games = relationship("Game", back_populates="league")


class LeagueMember(Base):
    __tablename__ = "league_members"

    id = Column(String, primary_key=True, default=generate_uuid)
    league_id = Column(String, ForeignKey("leagues.id"), nullable=False)
    player_id = Column(String, ForeignKey("players.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    league = relationship("League", back_populates="members")
    player = relationship("Player", back_populates="league_memberships")

    __table_args__ = (
        UniqueConstraint("league_id", "player_id", name="uq_league_member"),
    )
