import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import KeywordRanking from './pages/KeywordRanking'
import DraftGeneration from './pages/DraftGeneration'
import SavedDrafts from './pages/SavedDrafts'
import TickerAnalysis from './pages/TickerAnalysis'
import './App.css'

function App(): React.JSX.Element {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/ticker" element={<TickerAnalysis />} />
        <Route path="/keywords/:weekKey" element={<KeywordRanking />} />
        <Route path="/draft/:rankingId" element={<DraftGeneration />} />
        <Route path="/drafts" element={<SavedDrafts />} />
      </Routes>
    </Layout>
  )
}

export default App
