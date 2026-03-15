"""Seed data route - North Hants Golf Club and other initial data."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Course, Hole, TeeSet, TeeHole

router = APIRouter(prefix="/api/seed", tags=["seed"])

# North Hants Golf Club - Fleet, Hampshire, UK
# Par 70, 18 holes
NORTH_HANTS_HOLES = [
    # (hole_number, par, stroke_index, yards_white)
    (1,  4, 7,  370),
    (2,  4, 11, 343),
    (3,  3, 15, 157),
    (4,  5, 3,  507),
    (5,  4, 1,  428),
    (6,  3, 13, 190),
    (7,  4, 9,  389),
    (8,  4, 5,  405),
    (9,  4, 17, 305),
    (10, 4, 4,  400),
    (11, 3, 16, 160),
    (12, 5, 10, 478),
    (13, 4, 2,  435),
    (14, 3, 18, 132),
    (15, 4, 8,  360),
    (16, 4, 12, 330),
    (17, 4, 6,  395),
    (18, 4, 14, 350),
]

NORTH_HANTS_TEE_SETS = [
    {
        "name": "White",
        "color": "#FFFFFF",
        "course_rating": 70.2,
        "slope_rating": 128,
        "yards": [370, 343, 157, 507, 428, 190, 389, 405, 305, 400, 160, 478, 435, 132, 360, 330, 395, 350],
    },
    {
        "name": "Yellow",
        "color": "#FFD700",
        "course_rating": 68.8,
        "slope_rating": 124,
        "yards": [355, 330, 145, 490, 415, 178, 375, 390, 290, 385, 148, 465, 420, 120, 345, 318, 380, 335],
    },
    {
        "name": "Red",
        "color": "#FF0000",
        "course_rating": 71.2,
        "slope_rating": 126,
        "yards": [320, 295, 125, 450, 380, 155, 340, 355, 265, 350, 130, 430, 385, 105, 310, 290, 345, 305],
    },
]


@router.post("/north-hants")
async def seed_north_hants(db: AsyncSession = Depends(get_db)):
    """Seed North Hants Golf Club data."""
    # Check if already exists
    result = await db.execute(select(Course).where(Course.name == "North Hants Golf Club"))
    existing = result.scalar_one_or_none()
    if existing:
        return {"ok": True, "message": "Already seeded", "course_id": existing.id}

    course = Course(
        name="North Hants Golf Club",
        location="Fleet, Hampshire",
        country="United Kingdom",
        num_holes=18,
        course_rating=70.2,
        slope_rating=128,
    )
    db.add(course)
    await db.flush()

    # Add holes
    for hole_num, par, si, yards in NORTH_HANTS_HOLES:
        hole = Hole(
            course_id=course.id,
            hole_number=hole_num,
            par=par,
            stroke_index=si,
            yards=yards,
        )
        db.add(hole)

    # Add tee sets
    for ts_data in NORTH_HANTS_TEE_SETS:
        tee_set = TeeSet(
            course_id=course.id,
            name=ts_data["name"],
            color=ts_data["color"],
            course_rating=ts_data["course_rating"],
            slope_rating=ts_data["slope_rating"],
            total_yards=sum(ts_data["yards"]),
        )
        db.add(tee_set)
        await db.flush()

        for i, yds in enumerate(ts_data["yards"]):
            tee_hole = TeeHole(
                tee_set_id=tee_set.id,
                hole_number=i + 1,
                yards=yds,
            )
            db.add(tee_hole)

    await db.commit()
    return {"ok": True, "message": "North Hants Golf Club seeded", "course_id": course.id}


@router.post("/all")
async def seed_all(db: AsyncSession = Depends(get_db)):
    """Seed all default data."""
    result = await seed_north_hants(db)
    return {"ok": True, "courses": [result]}
