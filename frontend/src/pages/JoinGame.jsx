import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export default function JoinGame() {
  const { code: urlCode } = useParams()
  const [code, setCode] = useState(urlCode || '')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    if (urlCode) handleJoin(urlCode)
  }, [urlCode])

  const handleJoin = async (gameCode) => {
    setError('')
    try {
      const game = await api.joinGame(gameCode || code)
      navigate(`/game/${game.id}`)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div style={{ maxWidth: 500, margin: '40px auto' }}>
      <div className="card text-center">
        <h1>Join a Game</h1>
        <p className="text-light mb-md">Enter the game code shared with you</p>
        <input
          value={code}
          onChange={e => setCode(e.target.value.toUpperCase())}
          placeholder="Enter game code"
          maxLength={8}
          style={{
            textAlign: 'center',
            fontFamily: 'monospace',
            fontSize: '1.5rem',
            fontWeight: 700,
            letterSpacing: 4,
            textTransform: 'uppercase',
          }}
        />
        {error && <p style={{ color: 'var(--red)', marginBottom: 12 }}>{error}</p>}
        <button
          className="btn btn-primary"
          style={{ width: '100%' }}
          onClick={() => handleJoin()}
          disabled={code.length < 4}
        >
          Join Game
        </button>
        <div className="mt-md">
          <button
            className="btn btn-gold"
            style={{ width: '100%' }}
            onClick={() => code && navigate(`/leaderboard/${code}`)}
            disabled={code.length < 4}
          >
            View Leaderboard Only
          </button>
        </div>
      </div>
    </div>
  )
}
