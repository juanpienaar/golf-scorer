import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export default function Home({ currentPlayer, setCurrentPlayer }) {
  const [players, setPlayers] = useState([])
  const [loginName, setLoginName] = useState('')
  const [loginPin, setLoginPin] = useState('')
  const [error, setError] = useState('')
  const [recentGames, setRecentGames] = useState([])
  const navigate = useNavigate()

  useEffect(() => {
    api.getGames().then(setRecentGames).catch(() => {})
  }, [])

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const player = await api.loginPlayer({ name: loginName, pin: loginPin || null })
      setCurrentPlayer(player)
    } catch (err) {
      setError(err.message)
    }
  }

  const formatLabel = (f) => f.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())

  return (
    <div>
      {!currentPlayer ? (
        <div className="card" style={{ maxWidth: 400, margin: '40px auto' }}>
          <h1 className="text-center">Welcome to Golf Scorer</h1>
          <p className="text-center text-light mb-md">Sign in or create a player to get started</p>
          <form onSubmit={handleLogin}>
            <label>Name</label>
            <input value={loginName} onChange={e => setLoginName(e.target.value)} placeholder="Your name" required />
            <label>PIN (optional)</label>
            <input type="password" value={loginPin} onChange={e => setLoginPin(e.target.value)} placeholder="4-6 digit PIN" maxLength={6} />
            {error && <p style={{ color: 'var(--red)', marginBottom: 12 }}>{error}</p>}
            <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>Sign In</button>
          </form>
          <p className="text-center text-sm mt-md text-light">
            Don't have an account? <Link to="/players">Create a player</Link> first.
          </p>
        </div>
      ) : (
        <>
          <div className="card">
            <div className="flex flex-between flex-center">
              <div>
                <h1 style={{ marginBottom: 4 }}>Welcome, {currentPlayer.name}</h1>
                <p className="text-light text-sm">Handicap: {currentPlayer.handicap}</p>
              </div>
              <div className="flex gap-sm">
                <Link to="/create" className="btn btn-primary">New Game</Link>
                <Link to="/join" className="btn btn-gold">Join Game</Link>
                <button className="btn btn-secondary btn-small" onClick={() => setCurrentPlayer(null)}>Sign Out</button>
              </div>
            </div>
          </div>

          <h2 className="mb-md">Recent Games</h2>
          {recentGames.length === 0 ? (
            <div className="card empty-state">
              <p>No games yet. Create your first game!</p>
              <Link to="/create" className="btn btn-primary">Create Game</Link>
            </div>
          ) : (
            <div className="grid grid-2">
              {recentGames.slice(0, 6).map(game => (
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
        </>
      )}
    </div>
  )
}
