"""
Golf scoring engine supporting multiple game formats.

Handles handicap calculations, stableford points, and format-specific scoring.
"""
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class HoleInfo:
    hole_number: int
    par: int
    stroke_index: int
    yards: Optional[int] = None


@dataclass
class PlayerScore:
    player_id: str
    player_name: str
    team: Optional[str] = None
    playing_handicap: float = 0.0
    hole_scores: Dict[int, int] = field(default_factory=dict)  # hole_num -> strokes


def calculate_playing_handicap(course_handicap: float, percentage: int = 100) -> int:
    """Calculate playing handicap from course handicap and percentage."""
    return round(course_handicap * percentage / 100)


def calculate_course_handicap(
    handicap_index: float,
    slope_rating: int = 113,
    course_rating: float = 72.0,
    par: int = 72
) -> float:
    """Calculate course handicap from handicap index."""
    return handicap_index * (slope_rating / 113) + (course_rating - par)


def get_handicap_strokes_per_hole(
    playing_handicap: int,
    holes: List[HoleInfo]
) -> Dict[int, int]:
    """
    Distribute handicap strokes across holes based on stroke index.
    Returns dict of hole_number -> extra strokes on that hole.
    """
    strokes = {h.hole_number: 0 for h in holes}
    num_holes = len(holes)

    if playing_handicap >= 0:
        remaining = playing_handicap
        # First pass: one stroke per hole in SI order
        sorted_holes = sorted(holes, key=lambda h: h.stroke_index)
        pass_num = 0
        while remaining > 0:
            for hole in sorted_holes:
                if remaining <= 0:
                    break
                strokes[hole.hole_number] += 1
                remaining -= 1
            pass_num += 1
    else:
        # Plus handicap: remove strokes from highest SI first
        remaining = abs(playing_handicap)
        sorted_holes = sorted(holes, key=lambda h: h.stroke_index, reverse=True)
        for hole in sorted_holes:
            if remaining <= 0:
                break
            strokes[hole.hole_number] -= 1
            remaining -= 1

    return strokes


def calculate_stableford_points(
    gross_strokes: int,
    par: int,
    handicap_strokes: int = 0
) -> int:
    """
    Calculate stableford points for a hole.
    Net score relative to par:
      2 under = 4 (Albatross/Double Eagle)
      1 under = 3 (Eagle/Birdie)
      level   = 2 (Par)
      1 over  = 1 (Bogey)
      2+ over = 0
    """
    net_strokes = gross_strokes - handicap_strokes
    diff = net_strokes - par
    points = max(0, 2 - diff)
    return points


def calculate_net_score(gross: int, handicap_strokes: int) -> int:
    """Calculate net score for a hole."""
    return gross - handicap_strokes


# ─── FORMAT SCORERS ──────────────────────────────────────────────

def score_strokeplay(
    players: List[PlayerScore],
    holes: List[HoleInfo],
    use_handicap: bool = True
) -> List[Dict]:
    """Score a strokeplay round. Lowest total wins."""
    results = []
    for p in players:
        hcp_strokes = get_handicap_strokes_per_hole(
            round(p.playing_handicap), holes
        ) if use_handicap else {h.hole_number: 0 for h in holes}

        gross_total = 0
        net_total = 0
        hole_details = []
        holes_played = 0

        for hole in holes:
            strokes = p.hole_scores.get(hole.hole_number)
            if strokes is not None:
                hs = hcp_strokes[hole.hole_number]
                net = calculate_net_score(strokes, hs)
                gross_total += strokes
                net_total += net
                holes_played += 1
                hole_details.append({
                    "hole_number": hole.hole_number,
                    "par": hole.par,
                    "stroke_index": hole.stroke_index,
                    "strokes": strokes,
                    "net_strokes": net,
                    "handicap_strokes": hs,
                    "to_par": net - hole.par,
                })
            else:
                hole_details.append({
                    "hole_number": hole.hole_number,
                    "par": hole.par,
                    "stroke_index": hole.stroke_index,
                    "strokes": None,
                    "net_strokes": None,
                    "handicap_strokes": hcp_strokes[hole.hole_number],
                    "to_par": None,
                })

        par_total = sum(h.par for h in holes)
        results.append({
            "player_id": p.player_id,
            "player_name": p.player_name,
            "team": p.team,
            "playing_handicap": p.playing_handicap,
            "holes_played": holes_played,
            "gross_total": gross_total if holes_played > 0 else None,
            "net_total": net_total if holes_played > 0 else None,
            "to_par": net_total - par_total if holes_played == len(holes) else (
                net_total - sum(h.par for h in holes if h.hole_number in p.hole_scores) if holes_played > 0 else None
            ),
            "thru": max(p.hole_scores.keys()) if p.hole_scores else 0,
            "hole_scores": hole_details,
        })

    # Sort by net total (lowest first), then gross
    results.sort(key=lambda r: (
        r["net_total"] if r["net_total"] is not None else 999,
        r["gross_total"] if r["gross_total"] is not None else 999,
    ))
    return results


def score_stableford(
    players: List[PlayerScore],
    holes: List[HoleInfo],
    use_handicap: bool = True
) -> List[Dict]:
    """Score a stableford round. Highest points wins."""
    results = []
    for p in players:
        hcp_strokes = get_handicap_strokes_per_hole(
            round(p.playing_handicap), holes
        ) if use_handicap else {h.hole_number: 0 for h in holes}

        total_points = 0
        hole_details = []
        holes_played = 0

        for hole in holes:
            strokes = p.hole_scores.get(hole.hole_number)
            if strokes is not None:
                hs = hcp_strokes[hole.hole_number]
                points = calculate_stableford_points(strokes, hole.par, hs)
                net = calculate_net_score(strokes, hs)
                total_points += points
                holes_played += 1
                hole_details.append({
                    "hole_number": hole.hole_number,
                    "par": hole.par,
                    "stroke_index": hole.stroke_index,
                    "strokes": strokes,
                    "net_strokes": net,
                    "stableford_points": points,
                    "handicap_strokes": hs,
                })
            else:
                hole_details.append({
                    "hole_number": hole.hole_number,
                    "par": hole.par,
                    "stroke_index": hole.stroke_index,
                    "strokes": None,
                    "net_strokes": None,
                    "stableford_points": None,
                    "handicap_strokes": hcp_strokes[hole.hole_number],
                })

        results.append({
            "player_id": p.player_id,
            "player_name": p.player_name,
            "team": p.team,
            "playing_handicap": p.playing_handicap,
            "holes_played": holes_played,
            "total_stableford": total_points,
            "thru": max(p.hole_scores.keys()) if p.hole_scores else 0,
            "hole_scores": hole_details,
        })

    results.sort(key=lambda r: -r["total_stableford"])
    return results


def score_better_ball(
    players: List[PlayerScore],
    holes: List[HoleInfo],
    use_handicap: bool = True,
    stableford: bool = False
) -> Tuple[List[Dict], List[Dict]]:
    """
    Better Ball (Four-Ball). Best net score/stableford from each team per hole.
    Returns (individual_results, team_results).
    """
    # Get individual scores first
    if stableford:
        individual = score_stableford(players, holes, use_handicap)
    else:
        individual = score_strokeplay(players, holes, use_handicap)

    # Group by team
    teams: Dict[str, List[Dict]] = {}
    for p in individual:
        team = p.get("team") or "No Team"
        if team not in teams:
            teams[team] = []
        teams[team].append(p)

    team_results = []
    for team_name, team_players in teams.items():
        team_score = 0
        team_hole_details = []

        for hole in holes:
            if stableford:
                # Best stableford points from team
                best = 0
                for tp in team_players:
                    for hs in tp["hole_scores"]:
                        if hs["hole_number"] == hole.hole_number and hs["stableford_points"] is not None:
                            best = max(best, hs["stableford_points"])
                team_score += best
                team_hole_details.append({
                    "hole_number": hole.hole_number,
                    "best_score": best,
                })
            else:
                # Best net score from team
                best_net = None
                for tp in team_players:
                    for hs in tp["hole_scores"]:
                        if hs["hole_number"] == hole.hole_number and hs["net_strokes"] is not None:
                            if best_net is None or hs["net_strokes"] < best_net:
                                best_net = hs["net_strokes"]
                if best_net is not None:
                    team_score += best_net
                team_hole_details.append({
                    "hole_number": hole.hole_number,
                    "best_net": best_net,
                })

        team_results.append({
            "team": team_name,
            "players": [tp["player_name"] for tp in team_players],
            "team_score": team_score,
            "team_stableford": team_score if stableford else None,
            "team_to_par": team_score - sum(h.par for h in holes) if not stableford else None,
            "hole_details": team_hole_details,
        })

    if stableford:
        team_results.sort(key=lambda t: -t["team_score"])
    else:
        team_results.sort(key=lambda t: t["team_score"])

    return individual, team_results


def score_combined_stableford(
    players: List[PlayerScore],
    holes: List[HoleInfo],
    use_handicap: bool = True
) -> Tuple[List[Dict], List[Dict]]:
    """Combined Team Stableford. Sum of all team members' stableford points."""
    individual = score_stableford(players, holes, use_handicap)

    teams: Dict[str, List[Dict]] = {}
    for p in individual:
        team = p.get("team") or "No Team"
        if team not in teams:
            teams[team] = []
        teams[team].append(p)

    team_results = []
    for team_name, team_players in teams.items():
        total = sum(tp["total_stableford"] for tp in team_players)
        team_results.append({
            "team": team_name,
            "players": [tp["player_name"] for tp in team_players],
            "team_stableford": total,
        })

    team_results.sort(key=lambda t: -t["team_stableford"])
    return individual, team_results


def score_foursomes(
    players: List[PlayerScore],
    holes: List[HoleInfo],
    use_handicap: bool = True
) -> List[Dict]:
    """
    Foursomes (alternate shot). Two players share one ball.
    For scoring, scores are entered per team. Playing handicap = avg of team.
    We use the first player in each team as the score holder.
    """
    # Group by team - in foursomes, score is per team
    teams: Dict[str, List[PlayerScore]] = {}
    for p in players:
        team = p.team or p.player_name
        if team not in teams:
            teams[team] = []
        teams[team].append(p)

    results = []
    for team_name, team_players in teams.items():
        # Combined handicap is half the sum (or as specified)
        avg_hcp = sum(p.playing_handicap for p in team_players) / 2
        hcp_strokes = get_handicap_strokes_per_hole(
            round(avg_hcp), holes
        ) if use_handicap else {h.hole_number: 0 for h in holes}

        # Use first player's scores as team scores
        scorer = team_players[0]
        gross_total = 0
        net_total = 0
        holes_played = 0
        hole_details = []

        for hole in holes:
            strokes = scorer.hole_scores.get(hole.hole_number)
            if strokes is not None:
                hs = hcp_strokes[hole.hole_number]
                net = calculate_net_score(strokes, hs)
                gross_total += strokes
                net_total += net
                holes_played += 1
                hole_details.append({
                    "hole_number": hole.hole_number,
                    "par": hole.par,
                    "stroke_index": hole.stroke_index,
                    "strokes": strokes,
                    "net_strokes": net,
                    "handicap_strokes": hs,
                })
            else:
                hole_details.append({
                    "hole_number": hole.hole_number,
                    "par": hole.par,
                    "stroke_index": hole.stroke_index,
                    "strokes": None,
                    "net_strokes": None,
                    "handicap_strokes": hcp_strokes[hole.hole_number],
                })

        results.append({
            "team": team_name,
            "players": [p.player_name for p in team_players],
            "playing_handicap": avg_hcp,
            "holes_played": holes_played,
            "gross_total": gross_total if holes_played > 0 else None,
            "net_total": net_total if holes_played > 0 else None,
            "to_par": net_total - sum(h.par for h in holes) if holes_played == len(holes) else None,
            "thru": max(scorer.hole_scores.keys()) if scorer.hole_scores else 0,
            "hole_scores": hole_details,
        })

    results.sort(key=lambda r: r["net_total"] if r["net_total"] is not None else 999)
    return results


def score_skins(
    players: List[PlayerScore],
    holes: List[HoleInfo],
    use_handicap: bool = True,
    carry_over: bool = True,
    value_per_skin: int = 1
) -> Dict:
    """
    Skins game. Lowest net score on each hole wins the skin.
    Ties carry over to next hole if carry_over is True.
    """
    results = []
    pot = value_per_skin
    player_skins = {p.player_id: {"name": p.player_name, "skins": 0, "value": 0} for p in players}

    for hole in holes:
        best_net = None
        winner = None
        tied = False

        for p in players:
            strokes = p.hole_scores.get(hole.hole_number)
            if strokes is None:
                continue

            if use_handicap:
                hcp_strokes = get_handicap_strokes_per_hole(round(p.playing_handicap), holes)
                net = strokes - hcp_strokes[hole.hole_number]
            else:
                net = strokes

            if best_net is None or net < best_net:
                best_net = net
                winner = p
                tied = False
            elif net == best_net:
                tied = True

        if tied or winner is None:
            if carry_over:
                pot += value_per_skin
            results.append({
                "hole_number": hole.hole_number,
                "winner": None,
                "carry_over": carry_over,
                "value": pot if carry_over else value_per_skin,
            })
        else:
            player_skins[winner.player_id]["skins"] += 1
            player_skins[winner.player_id]["value"] += pot
            results.append({
                "hole_number": hole.hole_number,
                "winner": winner.player_name,
                "carry_over": False,
                "value": pot,
            })
            pot = value_per_skin

    return {
        "holes": results,
        "standings": sorted(
            player_skins.values(),
            key=lambda x: -x["value"]
        ),
    }


def score_wolfie(
    players: List[PlayerScore],
    holes: List[HoleInfo],
    use_handicap: bool = True,
    base_points: int = 1
) -> Dict:
    """
    Wolf game. On each hole, one player is the Wolf.
    Wolf can pick a partner or go lone wolf.
    Rotation order determines who is wolf on each hole.
    Scoring: Wolf picks after seeing tee shots. If lone wolf wins, double points.

    For simplicity in the app, we track:
    - Who was wolf on each hole
    - Who wolf picked (if any)
    - Net scores determine winner
    """
    num_players = len(players)
    if num_players < 3 or num_players > 4:
        return {"error": "Wolfie requires 3-4 players"}

    results = []
    point_totals = {p.player_id: {"name": p.player_name, "points": 0} for p in players}

    for hole in holes:
        wolf_idx = (hole.hole_number - 1) % num_players
        wolf = players[wolf_idx]

        # Calculate net scores for all players
        hole_nets = {}
        for p in players:
            strokes = p.hole_scores.get(hole.hole_number)
            if strokes is not None:
                if use_handicap:
                    hcp = get_handicap_strokes_per_hole(round(p.playing_handicap), holes)
                    hole_nets[p.player_id] = strokes - hcp[hole.hole_number]
                else:
                    hole_nets[p.player_id] = strokes

        results.append({
            "hole_number": hole.hole_number,
            "wolf": wolf.player_name,
            "wolf_id": wolf.player_id,
            "net_scores": {p.player_name: hole_nets.get(p.player_id) for p in players},
        })

    return {
        "holes": results,
        "standings": sorted(
            point_totals.values(),
            key=lambda x: -x["points"]
        ),
        "note": "Wolf partnerships and point allocation should be managed in the UI"
    }


def score_perch(
    players: List[PlayerScore],
    holes: List[HoleInfo],
    use_handicap: bool = True
) -> Dict:
    """
    Perch (King of the Hill). One player is 'on the perch'.
    To take the perch, beat the current perch holder.
    Player on the perch at the end of the round wins.
    Points: 1 point per hole you hold the perch.
    """
    perch_holder = None
    perch_points = {p.player_id: {"name": p.player_name, "perch_holes": 0, "times_on_perch": 0} for p in players}
    results = []

    for hole in holes:
        best_net = None
        best_player = None
        tied = False

        for p in players:
            strokes = p.hole_scores.get(hole.hole_number)
            if strokes is None:
                continue
            if use_handicap:
                hcp = get_handicap_strokes_per_hole(round(p.playing_handicap), holes)
                net = strokes - hcp[hole.hole_number]
            else:
                net = strokes

            if best_net is None or net < best_net:
                best_net = net
                best_player = p
                tied = False
            elif net == best_net:
                tied = True

        if not tied and best_player is not None:
            if perch_holder is None or best_player.player_id != perch_holder:
                perch_holder = best_player.player_id
                perch_points[perch_holder]["times_on_perch"] += 1

        if perch_holder:
            perch_points[perch_holder]["perch_holes"] += 1

        results.append({
            "hole_number": hole.hole_number,
            "perch_holder": perch_points[perch_holder]["name"] if perch_holder else None,
            "best_score": best_player.player_name if best_player and not tied else None,
            "tied": tied,
        })

    return {
        "holes": results,
        "standings": sorted(
            perch_points.values(),
            key=lambda x: -x["perch_holes"]
        ),
    }


def score_texas_scramble(
    players: List[PlayerScore],
    holes: List[HoleInfo],
    use_handicap: bool = True
) -> List[Dict]:
    """
    Texas Scramble. Team plays best ball off the tee, then best from there.
    One score per team per hole. Handicap = percentage of combined team handicap.
    Typically 10% of combined handicaps.
    Scores entered per team (first player is scorer).
    """
    # Same as foursomes scoring structure, just different handicap calc
    teams: Dict[str, List[PlayerScore]] = {}
    for p in players:
        team = p.team or "Team 1"
        if team not in teams:
            teams[team] = []
        teams[team].append(p)

    results = []
    for team_name, team_players in teams.items():
        # Combined handicap at 10% for scramble
        combined_hcp = sum(p.playing_handicap for p in team_players) * 0.10
        hcp_strokes = get_handicap_strokes_per_hole(
            round(combined_hcp), holes
        ) if use_handicap else {h.hole_number: 0 for h in holes}

        scorer = team_players[0]
        gross_total = 0
        net_total = 0
        holes_played = 0
        hole_details = []

        for hole in holes:
            strokes = scorer.hole_scores.get(hole.hole_number)
            if strokes is not None:
                hs = hcp_strokes[hole.hole_number]
                net = calculate_net_score(strokes, hs)
                gross_total += strokes
                net_total += net
                holes_played += 1
                hole_details.append({
                    "hole_number": hole.hole_number,
                    "strokes": strokes,
                    "net_strokes": net,
                    "handicap_strokes": hs,
                })

        results.append({
            "team": team_name,
            "players": [p.player_name for p in team_players],
            "playing_handicap": combined_hcp,
            "holes_played": holes_played,
            "gross_total": gross_total,
            "net_total": net_total,
            "hole_scores": hole_details,
        })

    results.sort(key=lambda r: r["net_total"] if r["net_total"] else 999)
    return results


def score_match_play(
    players: List[PlayerScore],
    holes: List[HoleInfo],
    use_handicap: bool = True
) -> Dict:
    """
    Match Play. Hole-by-hole comparison. Win, lose, or halve each hole.
    Supports 2 players or 2 teams.
    """
    if len(players) < 2:
        return {"error": "Match play requires at least 2 players"}

    # For simplicity, compare first two players (or teams)
    p1 = players[0]
    p2 = players[1]

    results = []
    p1_up = 0

    for hole in holes:
        s1 = p1.hole_scores.get(hole.hole_number)
        s2 = p2.hole_scores.get(hole.hole_number)

        if s1 is None or s2 is None:
            results.append({
                "hole_number": hole.hole_number,
                "result": "not_played",
                "match_status": f"{'All Square' if p1_up == 0 else f'{p1.player_name} {p1_up} UP' if p1_up > 0 else f'{p2.player_name} {abs(p1_up)} UP'}",
            })
            continue

        if use_handicap:
            hcp1 = get_handicap_strokes_per_hole(round(p1.playing_handicap), holes)
            hcp2 = get_handicap_strokes_per_hole(round(p2.playing_handicap), holes)
            net1 = s1 - hcp1[hole.hole_number]
            net2 = s2 - hcp2[hole.hole_number]
        else:
            net1 = s1
            net2 = s2

        if net1 < net2:
            p1_up += 1
            winner = p1.player_name
        elif net2 < net1:
            p1_up -= 1
            winner = p2.player_name
        else:
            winner = "halved"

        remaining = len(holes) - hole.hole_number
        dormie = abs(p1_up) == remaining
        match_over = abs(p1_up) > remaining

        status = "All Square"
        if p1_up > 0:
            status = f"{p1.player_name} {p1_up} UP"
        elif p1_up < 0:
            status = f"{p2.player_name} {abs(p1_up)} UP"

        results.append({
            "hole_number": hole.hole_number,
            "p1_net": net1,
            "p2_net": net2,
            "winner": winner,
            "match_status": status,
            "dormie": dormie,
            "match_over": match_over,
        })

        if match_over:
            break

    final_status = "All Square"
    if p1_up > 0:
        final_status = f"{p1.player_name} wins"
    elif p1_up < 0:
        final_status = f"{p2.player_name} wins"

    return {
        "player1": p1.player_name,
        "player2": p2.player_name,
        "holes": results,
        "final_status": final_status,
        "score": p1_up,
    }


def score_flags(
    players: List[PlayerScore],
    holes: List[HoleInfo],
    use_handicap: bool = True
) -> List[Dict]:
    """
    Flags game. Each player gets par + handicap strokes.
    Play until you run out of strokes. Furthest player wins.
    """
    results = []
    for p in players:
        total_strokes_allowed = sum(h.par for h in holes) + (round(p.playing_handicap) if use_handicap else 0)
        strokes_used = 0
        furthest_hole = 0

        for hole in holes:
            s = p.hole_scores.get(hole.hole_number)
            if s is None:
                break
            strokes_used += s
            if strokes_used <= total_strokes_allowed:
                furthest_hole = hole.hole_number
            else:
                # Partial hole
                remaining = total_strokes_allowed - (strokes_used - s)
                results.append({
                    "player_id": p.player_id,
                    "player_name": p.player_name,
                    "total_strokes_allowed": total_strokes_allowed,
                    "finished_hole": furthest_hole,
                    "strokes_into_next": remaining,
                    "flag_position": f"Hole {hole.hole_number}, {remaining} strokes in",
                })
                break
        else:
            # Completed all holes
            remaining = total_strokes_allowed - strokes_used
            results.append({
                "player_id": p.player_id,
                "player_name": p.player_name,
                "total_strokes_allowed": total_strokes_allowed,
                "finished_hole": len(holes),
                "strokes_remaining": remaining,
                "flag_position": f"Finished with {remaining} strokes to spare",
            })

    results.sort(key=lambda r: (-r.get("finished_hole", 0), -r.get("strokes_remaining", r.get("strokes_into_next", 0))))
    return results


# ─── MASTER SCORER ───────────────────────────────────────────────

def score_game(
    format: str,
    players: List[PlayerScore],
    holes: List[HoleInfo],
    use_handicap: bool = True
) -> Dict:
    """Route to appropriate scoring function based on format."""
    scorers = {
        "strokeplay": lambda: {"individual": score_strokeplay(players, holes, use_handicap)},
        "stableford": lambda: {"individual": score_stableford(players, holes, use_handicap)},
        "better_ball_fourball": lambda: dict(zip(
            ["individual", "teams"],
            score_better_ball(players, holes, use_handicap, stableford=False)
        )),
        "better_ball_stableford": lambda: dict(zip(
            ["individual", "teams"],
            score_better_ball(players, holes, use_handicap, stableford=True)
        )),
        "combined_team_stableford": lambda: dict(zip(
            ["individual", "teams"],
            score_combined_stableford(players, holes, use_handicap)
        )),
        "foursomes": lambda: {"teams": score_foursomes(players, holes, use_handicap)},
        "wolfie": lambda: score_wolfie(players, holes, use_handicap),
        "perch": lambda: score_perch(players, holes, use_handicap),
        "skins": lambda: score_skins(players, holes, use_handicap),
        "match_play": lambda: score_match_play(players, holes, use_handicap),
        "texas_scramble": lambda: {"teams": score_texas_scramble(players, holes, use_handicap)},
        "flags": lambda: {"individual": score_flags(players, holes, use_handicap)},
        "greensomes": lambda: {"teams": score_foursomes(players, holes, use_handicap)},  # Same scoring as foursomes
        "chapman": lambda: {"teams": score_foursomes(players, holes, use_handicap)},
        "ambrose": lambda: {"teams": score_texas_scramble(players, holes, use_handicap)},
    }

    scorer = scorers.get(format)
    if not scorer:
        return {"error": f"Unknown format: {format}"}

    return scorer()
