import React, { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../api/client'

export default function Scorecard({ currentPlayer }) {
  const { gameId } = useParams()
  const [game, setGame] = useState(null)
  const [course, setCourse] = useState(null)
  const [scores, setScores] = useState({}) // { `${playerId}-${holeNum}`: strokes }
  const [currentHole, setCurrentHole] = useState(1)
  const [saving, setSaving] = useState(false)
  const [lastSaved, setLastSaved] = useState(null)

  useEffect(() => {
    const loadData = async () => {
      const gameData = await api.getGame(gameId)
      setGame(gameData)
      const courseData = await api.getCourse(gameData.course_id)
      setCourse(courseData)

      // Load existing scores
      const existingScores = await api.getScores(gameId)
      const scoreMap = {}
      existingScores.forEach(s => {
        if (s.strokes !== null) {
          scoreMap[`${s.player_id}-${s.hole_number}`] = s.strokes
        }
      })
      setScores(scoreMap)
    }
    loadData()
  }, [gameId])

  const setScore = (playerId, holeNum, value) => {
    const key = `${playerId}-${holeNum}`
    const strokes = parseInt(value)
    if (isNaN(strokes) || strokes < 1) {
      setScores(prev => { const next = { ...prev }; delete next[key]; return next })
    } else {
      setScores(prev => ({ ...prev, [key]: strokes }))
    }
  }

  const saveHoleScores = async (holeNum) => {
    setSaving(true)
    const entries = []
    game.players.forEach(p => {
      const key = `${p.player_id}-${holeNum}`
      if (scores[key] !== undefined) {
        entries.push({
          player_id: p.player_id,
          hole_number: holeNum,
          strokes: scores[key],
        })
      }
    })
    if (entries.length > 0) {
      await api.submitScoresBatch(gameId, { scores: entries })
      setLastSaved(new Date().toLocaleTimeString())
    }
    setSaving(false)
  }

  const saveAllAndNext = async () => {
    await saveHoleScores(currentHole)
    if (currentHole < (course?.num_holes || 18)) {
      setCurrentHole(currentHole + 1)
    }
  }

  const getScoreClass = (strokes, par) => {
    if (!strokes) return ''
    const diff = strokes - par
    if (diff <= -2) return 'score-eagle'
    if (diff === -1) return 'score-birdie'
    if (diff === 0) return 'score-par'
    if (diff === 1) return 'score-bogey'
    return 'score-double'
  }

  const getPlayerTotal = (playerId, upToHole) => {
    let total = 0
    for (let h = 1; h <= upToHole; h++) {
      const s = scores[`${playerId}-${h}`]
      if (s) total += s
    }
    return total
  }

  if (!game || !course) return <div className="card"><p>Loading scorecard...</p></div>

  const holes = course.holes.sort((a, b) => a.hole_number - b.hole_number)
  const currentHoleInfo = holes.find(h => h.hole_number === currentHole)
  const numHoles = game.num_holes || 18

  return (
    <div>
      <div className="flex flex-between flex-center mb-md">
        <h1>{game.course_name}</h1>
        <div className="flex gap-sm">
          <Link to={`/game/${gameId}/leaderboard`} className="btn btn-gold btn-small">Leaderboard</Link>
          <Link to={`/game/${gameId}`} className="btn btn-secondary btn-small">Back</Link>
        </div>
      </div>

      {/* Hole selector */}
      <div className="card" style={{ padding: '12px' }}>
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', justifyContent: 'center' }}>
          {holes.slice(0, numHoles).map(h => {
            const allScored = game.players.every(p => scores[`${p.player_id}-${h.hole_number}`] !== undefined)
            return (
              <button
                key={h.hole_number}
                onClick={() => { saveHoleScores(currentHole); setCurrentHole(h.hole_number) }}
                style={{
                  width: 36, height: 36, borderRadius: '50%', border: 'none',
                  background: h.hole_number === currentHole ? 'var(--green)' : allScored ? '#e8f5e9' : '#f5f5f5',
                  color: h.hole_number === currentHole ? '#fff' : 'var(--text)',
                  fontWeight: h.hole_number === currentHole ? 700 : 500,
                  cursor: 'pointer', fontSize: '0.85rem',
                }}
              >
                {h.hole_number}
              </button>
            )
          })}
        </div>
      </div>

      {/* Current hole scoring */}
      {currentHoleInfo && (
        <div className="hole-card">
          <div className="hole-header">
            <span className="hole-num">Hole {currentHole}</span>
            <div className="hole-info">
              <span>Par {currentHoleInfo.par}</span>
              <span>SI {currentHoleInfo.stroke_index}</span>
              {currentHoleInfo.yards && <span>{currentHoleInfo.yards}y</span>}
            </div>
          </div>

          {game.players.map(p => {
            const key = `${p.player_id}-${currentHole}`
            const value = scores[key] ?? ''
            const runningTotal = getPlayerTotal(p.player_id, currentHole)
            return (
              <div key={p.player_id} className="player-score-row">
                <div>
                  <span style={{ fontWeight: 600 }}>{p.player_name}</span>
                  <span className="text-sm text-light" style={{ marginLeft: 8 }}>HCP: {p.playing_handicap}</span>
                  {runningTotal > 0 && (
                    <span className="text-sm text-light" style={{ marginLeft: 8 }}>Total: {runningTotal}</span>
                  )}
                </div>
                <div className="flex gap-sm flex-center">
                  <button
                    className="btn btn-secondary btn-small"
                    onClick={() => setScore(p.player_id, currentHole, (parseInt(value) || currentHoleInfo.par + 1) - 1)}
                    style={{ width: 36, height: 36, borderRadius: '50%', padding: 0 }}
                  >-</button>
                  <input
                    className={`score-input ${getScoreClass(value, currentHoleInfo.par)}`}
                    type="number"
                    min="1"
                    max="15"
                    value={value}
                    onChange={e => setScore(p.player_id, currentHole, e.target.value)}
                    placeholder={currentHoleInfo.par.toString()}
                    style={{ border: `2px solid ${value ? (value <= currentHoleInfo.par ? 'var(--green)' : 'var(--red)') : 'var(--border)'}` }}
                  />
                  <button
                    className="btn btn-secondary btn-small"
                    onClick={() => setScore(p.player_id, currentHole, (parseInt(value) || currentHoleInfo.par - 1) + 1)}
                    style={{ width: 36, height: 36, borderRadius: '50%', padding: 0 }}
                  >+</button>
                </div>
              </div>
            )
          })}

          <div className="flex gap-sm mt-md" style={{ justifyContent: 'space-between' }}>
            <button
              className="btn btn-secondary"
              disabled={currentHole === 1}
              onClick={() => { saveHoleScores(currentHole); setCurrentHole(currentHole - 1) }}
            >
              Previous
            </button>
            <div className="text-sm text-light" style={{ alignSelf: 'center' }}>
              {saving ? 'Saving...' : lastSaved ? `Saved ${lastSaved}` : ''}
            </div>
            <button className="btn btn-primary" onClick={saveAllAndNext}>
              {currentHole < numHoles ? 'Save & Next' : 'Save Scores'}
            </button>
          </div>
        </div>
      )}

      {/* Full scorecard table */}
      <div className="card mt-md">
        <h2>Full Scorecard</h2>
        <div className="scorecard-table">
          <table>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', position: 'sticky', left: 0, background: 'var(--green-dark)', zIndex: 2 }}>Player</th>
                {holes.slice(0, numHoles <= 9 ? 9 : 9).map(h => (
                  <th key={h.hole_number} className="score-cell">{h.hole_number}</th>
                ))}
                <th>Out</th>
                {numHoles > 9 && holes.slice(9, 18).map(h => (
                  <th key={h.hole_number} className="score-cell">{h.hole_number}</th>
                ))}
                {numHoles > 9 && <th>In</th>}
                <th>Tot</th>
              </tr>
              <tr style={{ background: '#f5f5f5' }}>
                <td style={{ textAlign: 'left', fontWeight: 600, position: 'sticky', left: 0, background: '#f5f5f5', zIndex: 2 }}>Par</td>
                {holes.slice(0, 9).map(h => <td key={h.hole_number}>{h.par}</td>)}
                <td style={{ fontWeight: 700 }}>{holes.slice(0, 9).reduce((s, h) => s + h.par, 0)}</td>
                {numHoles > 9 && holes.slice(9, 18).map(h => <td key={h.hole_number}>{h.par}</td>)}
                {numHoles > 9 && <td style={{ fontWeight: 700 }}>{holes.slice(9, 18).reduce((s, h) => s + h.par, 0)}</td>}
                <td style={{ fontWeight: 700 }}>{holes.slice(0, numHoles).reduce((s, h) => s + h.par, 0)}</td>
              </tr>
            </thead>
            <tbody>
              {game.players.map(p => {
                const outTotal = Array.from({ length: 9 }, (_, i) => scores[`${p.player_id}-${i + 1}`] || 0).reduce((a, b) => a + b, 0)
                const inTotal = numHoles > 9 ? Array.from({ length: 9 }, (_, i) => scores[`${p.player_id}-${i + 10}`] || 0).reduce((a, b) => a + b, 0) : 0
                return (
                  <tr key={p.player_id}>
                    <td style={{ textAlign: 'left', fontWeight: 600, position: 'sticky', left: 0, background: '#fff', zIndex: 2, whiteSpace: 'nowrap' }}>
                      {p.player_name}
                    </td>
                    {holes.slice(0, 9).map(h => {
                      const s = scores[`${p.player_id}-${h.hole_number}`]
                      return (
                        <td key={h.hole_number} className={`score-cell ${getScoreClass(s, h.par)}`}>
                          {s || '-'}
                        </td>
                      )
                    })}
                    <td style={{ fontWeight: 700 }}>{outTotal || '-'}</td>
                    {numHoles > 9 && holes.slice(9, 18).map(h => {
                      const s = scores[`${p.player_id}-${h.hole_number}`]
                      return (
                        <td key={h.hole_number} className={`score-cell ${getScoreClass(s, h.par)}`}>
                          {s || '-'}
                        </td>
                      )
                    })}
                    {numHoles > 9 && <td style={{ fontWeight: 700 }}>{inTotal || '-'}</td>}
                    <td style={{ fontWeight: 700 }}>{(outTotal + inTotal) || '-'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
