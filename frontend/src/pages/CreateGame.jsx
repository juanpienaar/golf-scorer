import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const FORMATS = [
  { value: 'strokeplay', label: 'Strokeplay', desc: 'Lowest total score wins' },
  { value: 'stableford', label: 'Stableford', desc: 'Points-based scoring (highest wins)' },
  { value: 'better_ball_fourball', label: 'Better Ball (Fourball)', desc: 'Best net score from each team per hole' },
  { value: 'better_ball_stableford', label: 'Better Ball Stableford', desc: 'Best stableford points from each team per hole' },
  { value: 'foursomes', label: 'Foursomes', desc: 'Alternate shot - one ball per team' },
  { value: 'combined_team_stableford', label: 'Combined Team Stableford', desc: 'Sum of all team members stableford points' },
  { value: 'wolfie', label: 'Wolfie', desc: 'Rotating wolf picks partner each hole' },
  { value: 'perch', label: 'Perch', desc: 'King of the hill - hold the perch longest' },
  { value: 'skins', label: 'Skins', desc: 'Win individual holes outright' },
  { value: 'match_play', label: 'Match Play', desc: 'Hole-by-hole head-to-head' },
  { value: 'texas_scramble', label: 'Texas Scramble', desc: 'Team plays best ball each shot' },
  { value: 'greensomes', label: 'Greensomes', desc: 'Both tee off, pick best drive, alternate from there' },
  { value: 'chapman', label: 'Chapman / Pinehurst', desc: 'Both tee off, swap and play partner drive, pick best' },
  { value: 'ambrose', label: 'Ambrose', desc: 'Team scramble with handicap' },
  { value: 'flags', label: 'Flags', desc: 'Play until you run out of strokes (par + handicap)' },
]

const TEAM_FORMATS = ['better_ball_fourball', 'better_ball_stableford', 'foursomes', 'combined_team_stableford', 'texas_scramble', 'greensomes', 'chapman', 'ambrose']

export default function CreateGame({ currentPlayer }) {
  const [courses, setCourses] = useState([])
  const [players, setPlayers] = useState([])
  const [leagues, setLeagues] = useState([])
  const [courseId, setCourseId] = useState('')
  const [format, setFormat] = useState('stableford')
  const [useHandicap, setUseHandicap] = useState(true)
  const [handicapPct, setHandicapPct] = useState(100)
  const [numHoles, setNumHoles] = useState(18)
  const [leagueId, setLeagueId] = useState('')
  const [selectedPlayers, setSelectedPlayers] = useState([])
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    api.getCourses().then(setCourses).catch(() => {})
    api.getPlayers().then(setPlayers).catch(() => {})
    api.getLeagues().then(setLeagues).catch(() => {})
  }, [])

  const isTeamFormat = TEAM_FORMATS.includes(format)

  const togglePlayer = (playerId) => {
    setSelectedPlayers(prev => {
      const existing = prev.find(p => p.player_id === playerId)
      if (existing) return prev.filter(p => p.player_id !== playerId)
      const player = players.find(p => p.id === playerId)
      return [...prev, { player_id: playerId, name: player.name, team: '', playing_handicap: player.handicap }]
    })
  }

  const updatePlayerTeam = (playerId, team) => {
    setSelectedPlayers(prev => prev.map(p => p.player_id === playerId ? { ...p, team } : p))
  }

  const updatePlayerHandicap = (playerId, hcp) => {
    setSelectedPlayers(prev => prev.map(p => p.player_id === playerId ? { ...p, playing_handicap: parseFloat(hcp) || 0 } : p))
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!courseId) { alert('Select a course'); return }
    if (selectedPlayers.length === 0) { alert('Add at least one player'); return }
    setLoading(true)
    try {
      const game = await api.createGame({
        course_id: courseId,
        format,
        use_handicap: useHandicap,
        handicap_percentage: handicapPct,
        num_holes: numHoles,
        league_id: leagueId || null,
        created_by: currentPlayer?.id || null,
        players: selectedPlayers.map(p => ({
          player_id: p.player_id,
          team: p.team || null,
          playing_handicap: p.playing_handicap,
        })),
      })
      navigate(`/game/${game.id}`)
    } catch (err) { alert(err.message) }
    setLoading(false)
  }

  return (
    <div>
      <h1>Create New Game</h1>
      <form onSubmit={handleCreate}>
        <div className="card">
          <h2>Course</h2>
          {courses.length === 0 ? (
            <p className="text-light">No courses available. <a href="/courses">Add a course</a> first.</p>
          ) : (
            <select value={courseId} onChange={e => setCourseId(e.target.value)}>
              <option value="">Select a course...</option>
              {courses.map(c => <option key={c.id} value={c.id}>{c.name} ({c.num_holes} holes)</option>)}
            </select>
          )}
        </div>

        <div className="card">
          <h2>Format</h2>
          <select value={format} onChange={e => setFormat(e.target.value)}>
            {FORMATS.map(f => <option key={f.value} value={f.value}>{f.label} - {f.desc}</option>)}
          </select>

          <div className="form-row mt-md">
            <div>
              <label>Holes</label>
              <select value={numHoles} onChange={e => setNumHoles(parseInt(e.target.value))}>
                <option value={18}>18 Holes</option>
                <option value={9}>9 Holes</option>
              </select>
            </div>
            <div>
              <label>
                <input type="checkbox" checked={useHandicap} onChange={e => setUseHandicap(e.target.checked)} style={{ width: 'auto', marginRight: 8 }} />
                Use Handicaps
              </label>
              {useHandicap && (
                <>
                  <label className="mt-md">Handicap %</label>
                  <input type="number" value={handicapPct} onChange={e => setHandicapPct(parseInt(e.target.value))} min={0} max={100} />
                </>
              )}
            </div>
            <div>
              <label>League (optional)</label>
              <select value={leagueId} onChange={e => setLeagueId(e.target.value)}>
                <option value="">No league</option>
                {leagues.map(l => <option key={l.id} value={l.id}>{l.name} ({l.year})</option>)}
              </select>
            </div>
          </div>
        </div>

        <div className="card">
          <h2>Players</h2>
          <p className="text-sm text-light mb-md">Select players for this game. {isTeamFormat && 'Assign teams for team formats.'}</p>
          {players.length === 0 ? (
            <p className="text-light">No players. <a href="/players">Create players</a> first.</p>
          ) : (
            <div>
              {players.map(p => {
                const isSelected = selectedPlayers.some(sp => sp.player_id === p.id)
                const sp = selectedPlayers.find(sp => sp.player_id === p.id)
                return (
                  <div key={p.id} style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                    <div className="flex flex-center gap-sm">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => togglePlayer(p.id)}
                        style={{ width: 'auto' }}
                      />
                      <span style={{ fontWeight: 600, flex: 1 }}>{p.name}</span>
                      {isSelected && (
                        <>
                          <div style={{ width: 80 }}>
                            <input
                              type="number"
                              step="0.1"
                              value={sp.playing_handicap}
                              onChange={e => updatePlayerHandicap(p.id, e.target.value)}
                              placeholder="HCP"
                              style={{ marginBottom: 0 }}
                            />
                          </div>
                          {isTeamFormat && (
                            <div style={{ width: 120 }}>
                              <input
                                value={sp.team}
                                onChange={e => updatePlayerTeam(p.id, e.target.value)}
                                placeholder="Team name"
                                style={{ marginBottom: 0 }}
                              />
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: 14, fontSize: '1.1rem' }} disabled={loading}>
          {loading ? 'Creating...' : 'Create Game'}
        </button>
      </form>
    </div>
  )
}
