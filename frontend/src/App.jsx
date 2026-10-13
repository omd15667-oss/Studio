import React, { useEffect, useState } from 'react'

function App() {
  const [tasks, setTasks] = useState([])
  const [goal, setGoal] = useState('')

  useEffect(() => {
    // placeholder: no auth in simple frontend; uses demo token from backend UI
  }, [])

  async function createTask() {
    const token = localStorage.getItem('batu_token')
    const res = await fetch('/api/v2/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': token ? `Bearer ${token}` : '' },
      body: JSON.stringify({ goal })
    })
    const data = await res.json()
    setTasks([data, ...tasks])
    setGoal('')
  }

  return (
    <div style={{ padding: 24 }}>
      <h1>BATU Studio (Frontend)</h1>
      <div>
        <textarea rows={4} value={goal} onChange={e => setGoal(e.target.value)} placeholder="Enter goal"></textarea>
        <button onClick={createTask}>Create Task</button>
      </div>
      <div style={{ marginTop: 20 }}>
        <h2>Tasks</h2>
        {tasks.map(t => (
          <div key={t.id} style={{ border: '1px solid #ddd', padding: 8, marginBottom: 8 }}>
            <strong>{t.goal}</strong>
            <div>State: {t.state}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App
