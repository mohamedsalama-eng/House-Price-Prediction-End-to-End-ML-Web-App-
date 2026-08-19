import React from 'react';
import { PredictionForm } from '../components/PredictionForm';

export const HomePage: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-4">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          AI Real Estate Valuation
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-300 bg-clip-text text-transparent mb-3">
          House Price Estimator
        </h1>
        <p className="text-slate-400 max-w-lg mx-auto text-sm sm:text-base">
          Get instant machine-learning powered real estate valuations across 80+ cities in India.
        </p>
      </div>

      {/* Form Card */}
      <PredictionForm />
    </div>
  );
};
