"""Seed data route - North Hants Golf Club and other initial data."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database import get_db
from models import Course, Hole, TeeSet, TeeHole

router = APIRouter(prefix="/api/seed", tags=["seed"])

# North Hants Golf Club - Fleet, Hampshire, UK
# Par 70 (Men) / Par 73 (Women), 18 holes
# From official scorecard
# Tee sets: Black (65), White (62), Green (57), Forward (52)

NORTH_HANTS_HOLES = [
    # (hole, par, SI, black, white, green, forward, w_par, w_SI)
    (1,  3, 12, 209, 197, 185, 143, 3, 11),
    (2,  4,  4, 431, 406, 384, 363, 5, 13),
    (3,  5,  6, 537, 527, 477, 444, 5,  5),
    (4,  4, 16, 332, 290, 279, 254, 4, 15),
    (5,  4,  2, 435, 425, 384, 346, 4,  1),
    (6,  4, 14, 370, 355, 311, 285, 4,  9),
    (7,  4,  8, 416, 402, 365, 301, 4,  3),
    (8,  3, 18, 116, 115, 102, 100, 3, 17),
    (9,  4, 10, 422, 404, 375, 367, 4,  7),
    (10, 3, 11, 194, 178, 164, 148, 3, 14),
    (11, 4,  7, 371, 355, 326, 322, 4,  6),
    (12, 4,  1, 446, 425, 419, 394, 5, 16),
    (13, 4, 15, 330, 312, 269, 262, 4, 10),
    (14, 4,  5, 371, 379, 331, 304, 4,  4),
    (15, 3, 17, 161, 149, 138, 124, 3, 18),
    (16, 4,  3, 424, 413, 393, 268, 5, 12),
    (17, 5, 13, 503, 484, 457, 434, 5,  2),
    (18, 4,  9, 422, 400, 361, 358, 4,  8),
]

NORTH_HANTS_TEE_SETS = [
    {"name": "Black (65)", "color": "#000000", "yard_idx": 3},
    {"name": "White (62)", "color": "#FFFFFF", "yard_idx": 4},
    {"name": "Green (57)", "color": "#006400", "yard_idx": 5},
    {"name": "Forward (52)", "color": "#4169E1", "yard_idx": 6},
]


@router.post("/north-hants")
async def seed_north_hants(db: AsyncSession = Depends(get_db)):
    """Seed North Hants Golf Club data. Re-seeds if already exists."""
    # Delete existing if present
    result = await db.execute(select(Course).where(Course.name == "North Hants Golf Club"))
    existing = result.scalar_one_or_none()
    if existing:
        # Delete related records first
        for hole in (await db.execute(select(Hole).where(Hole.course_id == existing.id))).scalars().all():
            await db.delete(hole)
        for ts in (await db.execute(select(TeeSet).where(TeeSet.course_id == existing.id))).scalars().all():
            for th in (await db.execute(select(TeeHole).where(TeeHole.tee_set_id == ts.id))).scalars().all():
                await db.delete(th)
            await db.delete(ts)
        await db.delete(existing)
        await db.flush()

    course = Course(
        name="North Hants Golf Club",
        location="Fleet, Hampshire",
        country="United Kingdom",
        num_holes=18,
        course_rating=71.5,
        slope_rating=131,
    )
    db.add(course)
    await db.flush()

    # Add holes (men's par and SI, white tee yardage as default)
    for h in NORTH_HANTS_HOLES:
        hole = Hole(
            course_id=course.id,
            hole_number=h[0],
            par=h[1],
            stroke_index=h[2],
            yards=h[4],  # White tee as default
        )
        db.add(hole)

    # Add tee sets with per-hole yardages
    for ts_data in NORTH_HANTS_TEE_SETS:
        yards_list = [h[ts_data["yard_idx"]] for h in NORTH_HANTS_HOLES]
        tee_set = TeeSet(
            course_id=course.id,
            name=ts_data["name"],
            color=ts_data["color"],
            total_yards=sum(yards_list),
        )
        db.add(tee_set)
        await db.flush()

        for i, yds in enumerate(yards_list):
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
