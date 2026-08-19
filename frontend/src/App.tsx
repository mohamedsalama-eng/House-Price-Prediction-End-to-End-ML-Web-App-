import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { ResultPage } from './pages/ResultPage';
import { NotFoundPage } from './pages/NotFoundPage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
        {/* Navigation Bar */}
        <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur sticky top-0 z-30">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-3 group">
              <span className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-base shadow-md shadow-indigo-500/20 group-hover:scale-105 transition">
                🏠
              </span>
              <span className="font-bold text-slate-100 text-base tracking-tight">
                PropValuate <span className="text-indigo-400 font-mono text-xs">AI</span>
              </span>
            </Link>

            <nav className="flex items-center gap-4 text-xs font-semibold text-slate-400">
              <Link to="/" className="hover:text-indigo-400 transition">
                Estimator
              </Link>
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noreferrer"
                className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition"
              >
                API Docs ↗
              </a>
            </nav>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-10">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/result" element={<ResultPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
          <div className="max-w-5xl mx-auto px-4">
            <p>House Price Prediction System • Powered by FastAPI & scikit-learn</p>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}
