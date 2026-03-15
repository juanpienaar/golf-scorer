import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'

export default function Leagues() {
  const [leagues, setLeagues] = useState([])
  const [name, setName] = useState('')
  const [year, setYear] = useState(new Date().getFullYear())
  const [bestOf, setBestOf] = useState(15)
  const [loading, setLoading] = useState(false)

  const load = () => api.getLeagues().then(setLeagues).catch(() => {})
  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.createLeague({ name, year: parseInt(year), best_of: parseInt(bestOf) })
      setName('')
      load()
    } catch (err) { alert(err.message) }
    setLoading(false)
  }

  return (
    <div>
      <h1>Leagues & Order of Merit</h1>

      <div className="card">
        <h2>Create League</h2>
        <form onSubmit={handleCreate}>
          <div className="form-row">
            <div>
              <label>League Name *</label>
              <input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Sunday Roll-Up 2026" required />
            </div>
            <div>
              <label>Year</label>
              <input type="number" value={year} onChange={e => setYear(e.target.value)} />
            </div>
            <div>
              <label>Best Of (scores)</label>
              <input type="number" value={bestOf} onChange={e => setBestOf(e.target.value)} min={1} max={52} />
            </div>
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading}>Create League</button>
        </form>
      </div>

      {leagues.length === 0 ? (
        <div className="card empty-state">
          <p>No leagues yet. Create one to start tracking your Order of Merit.</p>
        </div>
      ) : (
        <div className="grid grid-2">
          {leagues.map(l => (
            <Link to={`/league/${l.id}`} key={l.id} className="card" style={{ textDecoration: 'none', color: 'inherit' }}>
              <h3>{l.name}</h3>
              <p className="text-sm text-light">
                {l.year} &middot; Best {l.best_of} scores &middot; {l.member_count} members
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
