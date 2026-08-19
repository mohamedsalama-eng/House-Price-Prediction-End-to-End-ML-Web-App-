import React from 'react';
import { Link } from 'react-router-dom';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="max-w-lg mx-auto text-center py-20 px-4">
      <div className="p-8 bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl space-y-4">
        <span className="text-6xl font-black bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent block">
          404
        </span>
        <h2 className="text-xl font-bold text-slate-100">Page Not Found</h2>
        <p className="text-slate-400 text-sm">
          The requested page could not be located.
        </p>
        <div className="pt-4">
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl text-sm transition"
          >
            ← Return to Home
          </Link>
        </div>
      </div>
    </div>
  );
};
