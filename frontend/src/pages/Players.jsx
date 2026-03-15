import React, { useState, useEffect } from 'react'
import { api } from '../api/client'

export default function Players() {
  const [players, setPlayers] = useState([])
  const [name, setName] = useState('')
  const [pin, setPin] = useState('')
  const [handicap, setHandicap] = useState('')
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)

  const load = () => api.getPlayers().then(setPlayers).catch(() => {})

  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.createPlayer({
        name,
        pin: pin || null,
        handicap: parseFloat(handicap) || 0,
        email: email || null,
      })
      setName(''); setPin(''); setHandicap(''); setEmail('')
      load()
    } catch (err) {
      alert(err.message)
    }
    setLoading(false)
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this player?')) return
    await api.deletePlayer(id)
    load()
  }

  return (
    <div>
      <h1>Players</h1>
      <div className="card">
        <h2>Add Player</h2>
        <form onSubmit={handleCreate}>
          <div className="form-row">
            <div>
              <label>Name *</label>
              <input value={name} onChange={e => setName(e.target.value)} placeholder="Player name" required />
            </div>
            <div>
              <label>Handicap</label>
              <input type="number" step="0.1" value={handicap} onChange={e => setHandicap(e.target.value)} placeholder="0.0" />
            </div>
            <div>
              <label>PIN (optional)</label>
              <input type="password" value={pin} onChange={e => setPin(e.target.value)} placeholder="4-6 digits" maxLength={6} />
            </div>
            <div>
              <label>Email</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="email@example.com" />
            </div>
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Add Player'}
          </button>
        </form>
      </div>

      <div className="card">
        <h2>All Players ({players.length})</h2>
        {players.length === 0 ? (
          <p className="text-light">No players yet. Add one above.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>Name</th>
                <th>Handicap</th>
                <th>Email</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {players.map(p => (
                <tr key={p.id}>
                  <td style={{ textAlign: 'left', fontWeight: 600 }}>{p.name}</td>
                  <td>{p.handicap}</td>
                  <td className="text-sm text-light">{p.email || '-'}</td>
                  <td>
                    <button className="btn btn-danger btn-small" onClick={() => handleDelete(p.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
