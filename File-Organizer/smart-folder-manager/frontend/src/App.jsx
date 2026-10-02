import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Organize from './pages/Organize';
import Processing from './pages/Processing';
import Classification from './pages/Classification';
import BatchOperations from './pages/BatchOperations';
import Duplicates from './pages/Duplicates';
import History from './pages/History';
import Settings from './pages/Settings';
import './styles/global.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/organize" element={<Organize />} />
        <Route path="/processing" element={<Processing />} />
        <Route path="/classification" element={<Classification />} />
        <Route path="/batch-operations" element={<BatchOperations />} />
        <Route path="/duplicates" element={<Duplicates />} />
        <Route path="/history" element={<History />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Router>
  );
}

export default App;
