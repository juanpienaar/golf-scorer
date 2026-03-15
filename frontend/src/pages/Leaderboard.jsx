import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../api/client'

export default function Leaderboard() {
  const { gameId, code } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [autoRefresh, setAutoRefresh] = useState(true)

  const load = async () => {
    try {
      const result = code
        ? await api.getLeaderboardByCode(code)
        : await api.getLeaderboard(gameId)
      setData(result)
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => { load() }, [gameId, code])

  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(load, 15000) // Refresh every 15 seconds
    return () => clearInterval(interval)
  }, [autoRefresh, gameId, code])

  const formatLabel = (f) => f?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())

  if (error) return <div className="card"><p style={{ color: 'var(--red)' }}>{error}</p></div>
  if (!data) return <div className="card"><p>Loading leaderboard...</p></div>

  const results = data.results || {}
  const hasTeams = !!results.teams?.length
  const hasIndividual = !!results.individual?.length
  const isStableford = data.format?.includes('stableford') || data.format === 'stableford'
  const isSkins = data.format === 'skins'
  const isMatchPlay = data.format === 'match_play'
  const isPerch = data.format === 'perch'
  const isWolfie = data.format === 'wolfie'

  return (
    <div>
      <div className="flex flex-between flex-center mb-md">
        <div>
          <h1 style={{ marginBottom: 4 }}>Live Leaderboard</h1>
          <div className="flex gap-sm flex-center">
            <span className="text-sm text-light">{data.course_name}</span>
            <span className="format-tag">{formatLabel(data.format)}</span>
            <span className={`badge ${data.status === 'in_progress' ? 'badge-green' : 'badge-blue'}`}>
              {data.status?.replace('_', ' ')}
            </span>
          </div>
        </div>
        <div className="flex gap-sm">
          <button
            className={`btn btn-small ${autoRefresh ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          </button>
          <button className="btn btn-secondary btn-small" onClick={load}>Refresh</button>
          {gameId && <Link to={`/game/${gameId}/score`} className="btn btn-primary btn-small">Score</Link>}
        </div>
      </div>

      {/* Team Leaderboard */}
      {hasTeams && (
        <div className="card">
          <h2>Team Standings</h2>
          <table>
            <thead>
              <tr>
                <th>Pos</th>
                <th style={{ textAlign: 'left' }}>Team</th>
                <th style={{ textAlign: 'left' }}>Players</th>
                {isStableford ? <th>Points</th> : <th>Score</th>}
                {results.teams[0]?.team_to_par !== undefined && <th>To Par</th>}
              </tr>
            </thead>
            <tbody>
              {results.teams.map((team, i) => (
                <tr key={team.team}>
                  <td className="leaderboard-pos">{i + 1}</td>
                  <td className="leaderboard-name">{team.team}</td>
                  <td style={{ textAlign: 'left' }} className="text-sm">{team.players?.join(', ')}</td>
                  <td style={{ fontWeight: 700, fontSize: '1.1rem' }}>
                    {team.team_stableford ?? team.team_score ?? '-'}
                  </td>
                  {team.team_to_par !== undefined && (
                    <td style={{ color: team.team_to_par < 0 ? 'var(--birdie)' : team.team_to_par > 0 ? 'var(--bogey)' : 'var(--green)' }}>
                      {team.team_to_par > 0 ? '+' : ''}{team.team_to_par}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Skins */}
      {isSkins && results.holes && (
        <div className="card">
          <h2>Skins</h2>
          <table>
            <thead>
              <tr><th>Hole</th><th>Winner</th><th>Value</th></tr>
            </thead>
            <tbody>
              {results.holes.map(h => (
                <tr key={h.hole_number}>
                  <td>{h.hole_number}</td>
                  <td style={{ fontWeight: h.winner ? 700 : 400 }}>{h.winner || (h.carry_over ? 'Carry over' : 'No winner')}</td>
                  <td>{h.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {results.standings && (
            <>
              <h3 className="mt-md">Standings</h3>
              <table>
                <thead><tr><th style={{ textAlign: 'left' }}>Player</th><th>Skins</th><th>Value</th></tr></thead>
                <tbody>
                  {results.standings.map(s => (
                    <tr key={s.name}><td style={{ textAlign: 'left' }}>{s.name}</td><td>{s.skins}</td><td>{s.value}</td></tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}

      {/* Match Play */}
      {isMatchPlay && results.holes && (
        <div className="card">
          <h2>{results.player1} vs {results.player2}</h2>
          <p style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 16, color: 'var(--green-dark)' }}>
            {results.final_status}
          </p>
          <table>
            <thead>
              <tr><th>Hole</th><th>{results.player1}</th><th>{results.player2}</th><th>Result</th><th>Status</th></tr>
            </thead>
            <tbody>
              {results.holes.map(h => (
                <tr key={h.hole_number} style={h.match_over ? { background: '#e8f5e9' } : {}}>
                  <td>{h.hole_number}</td>
                  <td>{h.p1_net ?? '-'}</td>
                  <td>{h.p2_net ?? '-'}</td>
                  <td style={{ fontWeight: 600 }}>{h.winner || '-'}</td>
                  <td>{h.match_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Perch */}
      {isPerch && results.standings && (
        <div className="card">
          <h2>Perch Standings</h2>
          <table>
            <thead><tr><th>Pos</th><th style={{ textAlign: 'left' }}>Player</th><th>Holes on Perch</th><th>Times on Perch</th></tr></thead>
            <tbody>
              {results.standings.map((s, i) => (
                <tr key={s.name}>
                  <td className="leaderboard-pos">{i + 1}</td>
                  <td className="leaderboard-name">{s.name}</td>
                  <td style={{ fontWeight: 700, fontSize: '1.1rem' }}>{s.perch_holes}</td>
                  <td>{s.times_on_perch}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Individual Leaderboard */}
      {hasIndividual && (
        <div className="card">
          <h2>Individual Standings</h2>
          <table>
            <thead>
              <tr>
                <th>Pos</th>
                <th style={{ textAlign: 'left' }}>Player</th>
                <th>HCP</th>
                <th>Thru</th>
                {isStableford ? (
                  <th>Points</th>
                ) : (
                  <>
                    <th>Gross</th>
                    <th>Net</th>
                    <th>To Par</th>
                  </>
                )}
              </tr>
            </thead>
            <tbody>
              {results.individual.map((p, i) => (
                <tr key={p.player_id || p.player_name}>
                  <td className="leaderboard-pos">{i + 1}</td>
                  <td className="leaderboard-name">
                    {p.player_name}
                    {p.team && <span className="text-sm text-light"> ({p.team})</span>}
                  </td>
                  <td className="text-sm">{p.playing_handicap}</td>
                  <td>{p.thru || p.holes_played || '-'}</td>
                  {isStableford ? (
                    <td style={{ fontWeight: 700, fontSize: '1.1rem' }}>{p.total_stableford ?? '-'}</td>
                  ) : (
                    <>
                      <td>{p.gross_total ?? '-'}</td>
                      <td style={{ fontWeight: 700 }}>{p.net_total ?? '-'}</td>
                      <td style={{
                        fontWeight: 700,
                        color: p.to_par < 0 ? 'var(--birdie)' : p.to_par > 0 ? 'var(--bogey)' : 'var(--green)',
                      }}>
                        {p.to_par !== null && p.to_par !== undefined ? (p.to_par > 0 ? `+${p.to_par}` : p.to_par) : '-'}
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-center text-sm text-light mt-md">
        Last updated: {data.last_updated ? new Date(data.last_updated).toLocaleTimeString() : '-'}
        {autoRefresh && ' (auto-refreshing every 15s)'}
      </p>
    </div>
  )
}
