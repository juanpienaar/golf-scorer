import React, { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export default function GameView({ currentPlayer }) {
  const { gameId } = useParams()
  const [game, setGame] = useState(null)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    api.getGame(gameId).then(setGame).catch(err => setError(err.message))
  }, [gameId])

  const handleStart = async () => {
    await api.startGame(gameId)
    setGame({ ...game, status: 'in_progress' })
  }

  const handleComplete = async () => {
    if (!confirm('Mark this game as completed?')) return
    await api.completeGame(gameId)
    setGame({ ...game, status: 'completed' })
  }

  const formatLabel = (f) => f.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())

  if (error) return <div className="card"><p style={{ color: 'var(--red)' }}>{error}</p></div>
  if (!game) return <div className="card"><p>Loading...</p></div>

  const shareUrl = `${window.location.origin}/join/${game.game_code}`
  const leaderboardUrl = `${window.location.origin}/leaderboard/${game.game_code}`

  return (
    <div>
      <div className="card">
        <div className="flex flex-between flex-center mb-md">
          <div>
            <h1 style={{ marginBottom: 4 }}>{game.course_name}</h1>
            <div className="flex gap-sm flex-center">
              <span className="format-tag">{formatLabel(game.format)}</span>
              <span className={`badge ${game.status === 'in_progress' ? 'badge-green' : game.status === 'completed' ? 'badge-blue' : 'badge-gold'}`}>
                {game.status.replace('_', ' ')}
              </span>
              <span className="text-sm text-light">{game.date_played}</span>
            </div>
          </div>
        </div>

        <div className="text-center mb-md">
          <p className="text-sm text-light mb-sm">Share this code to let others score:</p>
          <div className="game-code">{game.game_code}</div>
          <div className="mt-md flex gap-sm" style={{ justifyContent: 'center', flexWrap: 'wrap' }}>
            <button className="btn btn-secondary btn-small" onClick={() => navigator.clipboard?.writeText(shareUrl)}>
              Copy Join Link
            </button>
            <button className="btn btn-secondary btn-small" onClick={() => navigator.clipboard?.writeText(leaderboardUrl)}>
              Copy Leaderboard Link
            </button>
          </div>
        </div>

        <div className="flex gap-sm" style={{ justifyContent: 'center', flexWrap: 'wrap' }}>
          {game.status === 'setup' && (
            <button className="btn btn-primary" onClick={handleStart}>Start Game</button>
          )}
          {(game.status === 'setup' || game.status === 'in_progress') && (
            <Link to={`/game/${gameId}/score`} className="btn btn-primary">Enter Scores</Link>
          )}
          <Link to={`/game/${gameId}/leaderboard`} className="btn btn-gold">Live Leaderboard</Link>
          {game.status === 'in_progress' && (
            <button className="btn btn-secondary" onClick={handleComplete}>Complete Game</button>
          )}
        </div>
      </div>

      <div className="card">
        <h2>Players ({game.players.length})</h2>
        <table>
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>Name</th>
              <th>Handicap</th>
              <th>Team</th>
            </tr>
          </thead>
          <tbody>
            {game.players.map(p => (
              <tr key={p.id}>
                <td style={{ textAlign: 'left', fontWeight: 600 }}>{p.player_name}</td>
                <td>{p.playing_handicap}</td>
                <td>{p.team || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {game.notes && (
        <div className="card">
          <h2>Notes</h2>
          <p>{game.notes}</p>
        </div>
      )}
    </div>
  )
}
