import { Link, Outlet } from 'react-router-dom'

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <Link to="/" className="brand">Shipment Document AI</Link>
        <span className="env">Analyst Review</span>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
