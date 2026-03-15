import React, { useState, useEffect } from 'react'
import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import Home from './pages/Home'
import Players from './pages/Players'
import Courses from './pages/Courses'
import CreateGame from './pages/CreateGame'
import GameView from './pages/GameView'
import Scorecard from './pages/Scorecard'
import Leaderboard from './pages/Leaderboard'
import JoinGame from './pages/JoinGame'
import Leagues from './pages/Leagues'
import LeagueDetail from './pages/LeagueDetail'
import GameList from './pages/GameList'

const STYLES = `
  * { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --green: #1b5e20;
    --green-light: #2e7d32;
    --green-dark: #0d3311;
    --gold: #ffd700;
    --bg: #f5f5f0;
    --card: #ffffff;
    --text: #1a1a1a;
    --text-light: #666;
    --border: #e0e0e0;
    --red: #c62828;
    --blue: #1565c0;
    --birdie: #1565c0;
    --eagle: #6a1b9a;
    --bogey: #c62828;
    --double: #b71c1c;
    --par-bg: #e8f5e9;
  }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }
  nav {
    background: var(--green-dark);
    padding: 0;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  }
  .nav-inner {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    padding: 0 16px;
    overflow-x: auto;
  }
  .nav-brand {
    color: var(--gold);
    font-weight: 700;
    font-size: 1.2rem;
    padding: 12px 16px 12px 0;
    text-decoration: none;
    white-space: nowrap;
  }
  .nav-links { display: flex; gap: 0; }
  .nav-links a {
    color: #fff;
    text-decoration: none;
    padding: 14px 14px;
    font-size: 0.9rem;
    white-space: nowrap;
    transition: background 0.2s;
  }
  .nav-links a:hover { background: var(--green-light); }
  .container { max-width: 1200px; margin: 0 auto; padding: 20px 16px; }
  .card {
    background: var(--card);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }
  h1 { font-size: 1.5rem; margin-bottom: 16px; color: var(--green-dark); }
  h2 { font-size: 1.2rem; margin-bottom: 12px; color: var(--green); }
  h3 { font-size: 1rem; margin-bottom: 8px; }
  .btn {
    display: inline-block;
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    transition: all 0.2s;
  }
  .btn-primary { background: var(--green); color: #fff; }
  .btn-primary:hover { background: var(--green-light); }
  .btn-secondary { background: var(--border); color: var(--text); }
  .btn-secondary:hover { background: #d0d0d0; }
  .btn-danger { background: var(--red); color: #fff; }
  .btn-small { padding: 6px 12px; font-size: 0.85rem; }
  .btn-gold { background: var(--gold); color: var(--green-dark); }
  input, select {
    padding: 10px 14px;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.95rem;
    width: 100%;
    margin-bottom: 12px;
  }
  input:focus, select:focus { outline: none; border-color: var(--green); }
  label { display: block; font-weight: 600; margin-bottom: 4px; font-size: 0.9rem; }
  .form-row { display: flex; gap: 12px; flex-wrap: wrap; }
  .form-row > * { flex: 1; min-width: 120px; }
  .grid { display: grid; gap: 16px; }
  .grid-2 { grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
  .grid-3 { grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); }
  table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
  th, td { padding: 8px 10px; text-align: center; border-bottom: 1px solid var(--border); }
  th { background: var(--green-dark); color: #fff; font-weight: 600; font-size: 0.8rem; position: sticky; top: 0; }
  .scorecard-table { overflow-x: auto; }
  .scorecard-table table { min-width: 800px; }
  .score-cell { min-width: 36px; }
  .score-birdie { color: var(--birdie); font-weight: 700; }
  .score-eagle { color: var(--eagle); font-weight: 700; }
  .score-bogey { color: var(--bogey); }
  .score-double { color: var(--double); font-weight: 700; }
  .score-par { color: var(--green); font-weight: 600; }
  .score-input {
    width: 48px;
    height: 48px;
    text-align: center;
    font-size: 1.2rem;
    font-weight: 700;
    padding: 4px;
    border-radius: 50%;
    margin: 0;
  }
  .hole-card {
    background: var(--card);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }
  .hole-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--green);
  }
  .hole-num { font-size: 1.5rem; font-weight: 800; color: var(--green-dark); }
  .hole-info { display: flex; gap: 16px; font-size: 0.85rem; color: var(--text-light); }
  .hole-info span { font-weight: 600; }
  .player-score-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 0;
  }
  .player-score-row + .player-score-row { border-top: 1px solid var(--border); }
  .badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
  }
  .badge-green { background: #e8f5e9; color: var(--green); }
  .badge-gold { background: #fff8e1; color: #f57f17; }
  .badge-blue { background: #e3f2fd; color: var(--blue); }
  .badge-red { background: #ffebee; color: var(--red); }
  .game-code {
    font-family: monospace;
    font-size: 1.8rem;
    font-weight: 800;
    letter-spacing: 4px;
    color: var(--green-dark);
    background: #e8f5e9;
    padding: 12px 24px;
    border-radius: 8px;
    display: inline-block;
  }
  .leaderboard-pos { font-weight: 800; font-size: 1.1rem; }
  .leaderboard-name { font-weight: 600; text-align: left; }
  .empty-state {
    text-align: center;
    padding: 40px;
    color: var(--text-light);
  }
  .empty-state p { margin-bottom: 16px; }
  .flex { display: flex; }
  .flex-between { justify-content: space-between; }
  .flex-center { align-items: center; }
  .gap-sm { gap: 8px; }
  .gap-md { gap: 16px; }
  .mb-sm { margin-bottom: 8px; }
  .mb-md { margin-bottom: 16px; }
  .mt-md { margin-top: 16px; }
  .text-center { text-align: center; }
  .text-light { color: var(--text-light); }
  .text-sm { font-size: 0.85rem; }
  .format-tag {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    background: var(--green);
    color: #fff;
  }
  @media (max-width: 600px) {
    .nav-inner { padding: 0 8px; }
    .nav-links a { padding: 14px 10px; font-size: 0.8rem; }
    .container { padding: 12px 8px; }
    .card { padding: 14px; }
    .form-row { flex-direction: column; }
    .score-input { width: 42px; height: 42px; }
  }
`

export default function App() {
  const [currentPlayer, setCurrentPlayer] = useState(() => {
    try { return JSON.parse(localStorage.getItem('currentPlayer')) } catch { return null }
  })

  useEffect(() => {
    if (currentPlayer) localStorage.setItem('currentPlayer', JSON.stringify(currentPlayer))
    else localStorage.removeItem('currentPlayer')
  }, [currentPlayer])

  return (
    <>
      <style>{STYLES}</style>
      <nav>
        <div className="nav-inner">
          <Link to="/" className="nav-brand">Golf Scorer</Link>
          <div className="nav-links">
            <Link to="/">Home</Link>
            <Link to="/games">Games</Link>
            <Link to="/create">New Game</Link>
            <Link to="/join">Join</Link>
            <Link to="/players">Players</Link>
            <Link to="/courses">Courses</Link>
            <Link to="/leagues">Leagues</Link>
          </div>
        </div>
      </nav>
      <div className="container">
        <Routes>
          <Route path="/" element={<Home currentPlayer={currentPlayer} setCurrentPlayer={setCurrentPlayer} />} />
          <Route path="/players" element={<Players />} />
          <Route path="/courses" element={<Courses />} />
          <Route path="/create" element={<CreateGame currentPlayer={currentPlayer} />} />
          <Route path="/games" element={<GameList />} />
          <Route path="/game/:gameId" element={<GameView currentPlayer={currentPlayer} />} />
          <Route path="/game/:gameId/score" element={<Scorecard currentPlayer={currentPlayer} />} />
          <Route path="/game/:gameId/leaderboard" element={<Leaderboard />} />
          <Route path="/join" element={<JoinGame />} />
          <Route path="/join/:code" element={<JoinGame />} />
          <Route path="/leaderboard/:code" element={<Leaderboard />} />
          <Route path="/leagues" element={<Leagues />} />
          <Route path="/league/:leagueId" element={<LeagueDetail />} />
        </Routes>
      </div>
    </>
  )
}
