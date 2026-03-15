import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'

export default function LeagueDetail() {
  const { leagueId } = useParams()
  const [league, setLeague] = useState(null)
  const [members, setMembers] = useState([])
  const [oom, setOom] = useState(null)
  const [players, setPlayers] = useState([])
  const [selectedPlayer, setSelectedPlayer] = useState('')
  const [tab, setTab] = useState('oom')

  useEffect(() => {
    api.getLeague(leagueId).then(setLeague)
    api.getLeagueMembers(leagueId).then(setMembers)
    api.getOrderOfMerit(leagueId).then(setOom).catch(() => {})
    api.getPlayers().then(setPlayers)
  }, [leagueId])

  const handleAddMember = async () => {
    if (!selectedPlayer) return
    try {
      await api.addLeagueMember(leagueId, selectedPlayer)
      api.getLeagueMembers(leagueId).then(setMembers)
      setSelectedPlayer('')
    } catch (err) { alert(err.message) }
  }

  const handleRemoveMember = async (playerId) => {
    if (!confirm('Remove this member?')) return
    await api.removeLeagueMember(leagueId, playerId)
    api.getLeagueMembers(leagueId).then(setMembers)
  }

  if (!league) return <div className="card"><p>Loading...</p></div>

  const nonMembers = players.filter(p => !members.some(m => m.player_id === p.id))

  return (
    <div>
      <h1>{league.name}</h1>
      <p className="text-light mb-md">
        {league.year} &middot; Best {league.best_of} scores &middot; {members.length} members
      </p>

      <div className="flex gap-sm mb-md">
        <button className={`btn ${tab === 'oom' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTab('oom')}>Order of Merit</button>
        <button className={`btn ${tab === 'members' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTab('members')}>Members</button>
      </div>

      {tab === 'oom' && (
        <div className="card">
          <h2>Order of Merit {league.year}</h2>
          {!oom || oom.entries?.length === 0 ? (
            <p className="text-light">No qualifying rounds yet. Play a league game to get started.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th style={{ textAlign: 'left' }}>Player</th>
                  <th>HCP</th>
                  <th>Rounds</th>
                  <th>Best Scores</th>
                  <th>Total</th>
                  <th>Avg</th>
                </tr>
              </thead>
              <tbody>
                {oom.entries.map(e => (
                  <tr key={e.player_id}>
                    <td className="leaderboard-pos">
                      {e.rank === 1 ? '🥇' : e.rank === 2 ? '🥈' : e.rank === 3 ? '🥉' : e.rank}
                    </td>
                    <td className="leaderboard-name">{e.player_name}</td>
                    <td>{e.handicap}</td>
                    <td>{e.qualifying_rounds}</td>
                    <td className="text-sm">
                      {e.best_scores?.length > 0 ? e.best_scores.join(', ') : '-'}
                    </td>
                    <td style={{ fontWeight: 700, fontSize: '1.1rem' }}>{e.total_points}</td>
                    <td>{e.average_points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <p className="text-sm text-light mt-md">
            Scores based on stableford points with handicap. Best {league.best_of} rounds count.
            A qualifying round requires at least one other league member in the same game.
          </p>
        </div>
      )}

      {tab === 'members' && (
        <div className="card">
          <h2>Members</h2>
          <div className="flex gap-sm mb-md">
            <select value={selectedPlayer} onChange={e => setSelectedPlayer(e.target.value)} style={{ marginBottom: 0 }}>
              <option value="">Add a player...</option>
              {nonMembers.map(p => <option key={p.id} value={p.id}>{p.name} (HCP: {p.handicap})</option>)}
            </select>
            <button className="btn btn-primary" onClick={handleAddMember} disabled={!selectedPlayer}>Add</button>
          </div>
          {members.length === 0 ? (
            <p className="text-light">No members yet. Add players to the league above.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left' }}>Name</th>
                  <th>Handicap</th>
                  <th>Joined</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {members.map(m => (
                  <tr key={m.player_id}>
                    <td style={{ textAlign: 'left', fontWeight: 600 }}>{m.player_name}</td>
                    <td>{m.handicap}</td>
                    <td className="text-sm text-light">{new Date(m.joined_at).toLocaleDateString()}</td>
                    <td>
                      <button className="btn btn-danger btn-small" onClick={() => handleRemoveMember(m.player_id)}>Remove</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}
