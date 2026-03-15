import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'

export default function GameList() {
  const [games, setGames] = useState([])
  const [filter, setFilter] = useState('')

  useEffect(() => {
    api.getGames(filter || undefined).then(setGames).catch(() => {})
  }, [filter])

  const formatLabel = (f) => f.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())

  return (
    <div>
      <div className="flex flex-between flex-center mb-md">
        <h1>Games</h1>
        <Link to="/create" className="btn btn-primary">New Game</Link>
      </div>

      <div className="flex gap-sm mb-md">
        {['', 'in_progress', 'completed', 'setup'].map(f => (
          <button
            key={f}
            className={`btn btn-small ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilter(f)}
          >
            {f ? formatLabel(f) : 'All'}
          </button>
        ))}
      </div>

      {games.length === 0 ? (
        <div className="card empty-state">
          <p>No games found.</p>
          <Link to="/create" className="btn btn-primary">Create a Game</Link>
        </div>
      ) : (
        <div className="grid grid-2">
          {games.map(game => (
            <Link to={`/game/${game.id}`} key={game.id} className="card" style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="flex flex-between flex-center mb-sm">
                <span className="format-tag">{formatLabel(game.format)}</span>
                <span className={`badge ${game.status === 'in_progress' ? 'badge-green' : game.status === 'completed' ? 'badge-blue' : 'badge-gold'}`}>
                  {game.status.replace('_', ' ')}
                </span>
              </div>
              <h3>{game.course_name}</h3>
              <p className="text-sm text-light">{game.date_played} &middot; {game.player_count} players</p>
              <p className="text-sm" style={{ fontFamily: 'monospace', marginTop: 4 }}>Code: {game.game_code}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
