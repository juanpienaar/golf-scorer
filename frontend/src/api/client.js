const API_BASE = 'https://golf-scorer-production.up.railway.app';

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export const api = {
  getPlayers: () => request('/api/players'),
  createPlayer: (data) => request('/api/players/', { method: 'POST', body: JSON.stringify(data) }),
  loginPlayer: (data) => request('/api/players/login', { method: 'POST', body: JSON.stringify(data) }),
  updatePlayer: (id, data) => request(`/api/players/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deletePlayer: (id) => request(`/api/players/${id}`, { method: 'DELETE' }),
  getCourses: () => request('/api/courses'),
  getCourse: (id) => request(`/api/courses/${id}`),
  getGames: (status) => request(`/api/games${status ? `?status=${status}` : ''}`),
  getGame: (id) => request(`/api/games/${id}`),
  createGame: (data) => request('/api/games/', { method: 'POST', body: JSON.stringify(data) }),
  joinGame: (code) => request(`/api/games/join/${code}`),
  addPlayerToGame: (gameId, data) => request(`/api/games/${gameId}/players`, { method: 'POST', body: JSON.stringify(data) }),
  startGame: (id) => request(`/api/games/${id}/start`, { method: 'POST' }),
  completeGame: (id) => request(`/api/games/${id}/complete`, { method: 'POST' }),
  submitScore: (gameId, data) => request(`/api/games/${gameId}/scores`, { method: 'POST', body: JSON.stringify(data) }),
  submitScoresBatch: (gameId, data) => request(`/api/games/${gameId}/scores/batch`, { method: 'POST', body: JSON.stringify(data) }),
  getScores: (gameId) => request(`/api/games/${gameId}/scores`),
  getLeaderboard: (gameId) => request(`/api/games/${gameId}/leaderboard`),
  getLeaderboardByCode: (code) => request(`/api/games/code/${code}/leaderboard`),
  getLeagues: () => request('/api/leagues'),
  getLeague: (id) => request(`/api/leagues/${id}`),
  createLeague: (data) => request('/api/leagues/', { method: 'POST', body: JSON.stringify(data) }),
  getLeagueMembers: (id) => request(`/api/leagues/${id}/members`),
  addLeagueMember: (leagueId, playerId) => request(`/api/leagues/${leagueId}/members?player_id=${playerId}`, { method: 'POST' }),
  removeLeagueMember: (leagueId, playerId) => request(`/api/leagues/${leagueId}/members/${playerId}`, { method: 'DELETE' }),
  getOrderOfMerit: (id) => request(`/api/leagues/${id}/order-of-merit`),
  seedAll: () => request('/api/seed/all', { method: 'POST' }),
  seedNorthHants: () => request('/api/seed/north-hants', { method: 'POST' }),
};
