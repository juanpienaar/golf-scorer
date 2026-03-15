import React, { useState, useEffect } from 'react'
import { api } from '../api/client'

export default function Courses() {
  const [courses, setCourses] = useState([])
  const [selected, setSelected] = useState(null)
  const [seeding, setSeeding] = useState(false)

  const load = () => api.getCourses().then(setCourses).catch(() => {})
  useEffect(() => { load() }, [])

  const handleSeed = async () => {
    setSeeding(true)
    try {
      await api.seedNorthHants()
      load()
    } catch (err) { alert(err.message) }
    setSeeding(false)
  }

  const handleSelect = async (id) => {
    if (selected?.id === id) { setSelected(null); return }
    const course = await api.getCourse(id)
    setSelected(course)
  }

  return (
    <div>
      <div className="flex flex-between flex-center mb-md">
        <h1>Courses</h1>
        <button className="btn btn-primary" onClick={handleSeed} disabled={seeding}>
          {seeding ? 'Seeding...' : 'Seed North Hants GC'}
        </button>
      </div>

      {courses.length === 0 ? (
        <div className="card empty-state">
          <p>No courses yet. Click "Seed North Hants GC" to add the first course.</p>
        </div>
      ) : (
        <div className="grid grid-2">
          {courses.map(c => (
            <div key={c.id} className="card" style={{ cursor: 'pointer' }} onClick={() => handleSelect(c.id)}>
              <h3>{c.name}</h3>
              <p className="text-sm text-light">{c.location} &middot; {c.num_holes} holes</p>
            </div>
          ))}
        </div>
      )}

      {selected && (
        <div className="card mt-md">
          <h2>{selected.name}</h2>
          <p className="text-sm text-light mb-md">
            {selected.location}, {selected.country} &middot;
            CR: {selected.course_rating} &middot; SR: {selected.slope_rating}
          </p>

          {selected.tee_sets?.length > 0 && (
            <div className="mb-md">
              <h3>Tee Sets</h3>
              <div className="flex gap-md" style={{ flexWrap: 'wrap', marginTop: 8 }}>
                {selected.tee_sets.map(ts => (
                  <div key={ts.id} className="badge" style={{ background: ts.color === '#FFFFFF' ? '#f5f5f5' : ts.color + '22', color: 'var(--text)', border: `2px solid ${ts.color}` }}>
                    {ts.name} &middot; {ts.total_yards}y &middot; CR {ts.course_rating} / SR {ts.slope_rating}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="scorecard-table">
            <table>
              <thead>
                <tr>
                  <th>Hole</th>
                  {selected.holes.map(h => <th key={h.hole_number}>{h.hole_number}</th>)}
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ fontWeight: 600 }}>Par</td>
                  {selected.holes.map(h => <td key={h.hole_number}>{h.par}</td>)}
                  <td style={{ fontWeight: 700 }}>{selected.holes.reduce((s, h) => s + h.par, 0)}</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>SI</td>
                  {selected.holes.map(h => <td key={h.hole_number}>{h.stroke_index}</td>)}
                  <td>-</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>Yards</td>
                  {selected.holes.map(h => <td key={h.hole_number}>{h.yards}</td>)}
                  <td style={{ fontWeight: 700 }}>{selected.holes.reduce((s, h) => s + (h.yards || 0), 0)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
