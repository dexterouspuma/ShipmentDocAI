import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import ReviewQueue from './components/ReviewQueue'
import DocumentReview from './components/DocumentReview'
import './styles.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<ReviewQueue />} />
          <Route path="documents/:id" element={<DocumentReview />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)
