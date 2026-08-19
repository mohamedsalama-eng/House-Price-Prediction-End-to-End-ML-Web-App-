import React from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { PredictionResponse, PredictionRequest } from '../types/prediction';

interface LocationState {
  prediction?: PredictionResponse;
  property?: PredictionRequest;
}

export const ResultPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as LocationState | undefined;

  const prediction = state?.prediction;
  const property = state?.property;

  if (!prediction) {
    return (
      <div className="max-w-xl mx-auto text-center py-16 px-4">
        <div className="p-8 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl space-y-4">
          <span className="text-4xl">⚠️</span>
          <h2 className="text-xl font-bold text-slate-100">No Valuation Data Found</h2>
          <p className="text-slate-400 text-sm">
            It looks like you navigated here directly or the session expired. Please enter property details on the home page first.
          </p>
          <div className="pt-2">
            <Link
              to="/"
              className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl text-sm transition"
            >
              ← Go to Property Estimator
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fadeIn">
      {/* Result Hero Banner */}
      <div className="relative overflow-hidden bg-gradient-to-br from-emerald-950/60 via-slate-900 to-slate-950 border border-emerald-500/30 rounded-3xl p-8 sm:p-12 text-center shadow-2xl backdrop-blur-xl">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-5">
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          Valuation Result
        </div>

        <h1 className="text-sm font-semibold text-slate-400 uppercase tracking-widest mb-2">
          Estimated Market Price
        </h1>

        <div className="text-5xl sm:text-6xl font-black bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-200 bg-clip-text text-transparent mb-3 tracking-tight">
          {prediction.formatted_price || `₹${Math.round(prediction.predicted_price).toLocaleString('en-IN')}`}
        </div>

        <p className="text-slate-400 font-mono text-sm">
          Precise Value: ₹{Math.round(prediction.predicted_price).toLocaleString('en-IN')}
        </p>
      </div>

      {/* Property Breakdown Card */}
      {property && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 backdrop-blur shadow-xl">
          <h3 className="text-base font-bold text-slate-100 mb-6 flex items-center gap-2">
            <span>📋</span> Property Attributes Summary
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
            <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80">
              <span className="text-slate-500 text-xs block">Location</span>
              <span className="font-semibold text-slate-200 capitalize">
                {property.location} {property.locality ? `(${property.locality})` : ''}
              </span>
            </div>

            <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80">
              <span className="text-slate-500 text-xs block">Carpet / Super Area</span>
              <span className="font-semibold text-slate-200">
                {property.carpet_area ? `${property.carpet_area} sqft` : (property.super_area ? `${property.super_area} sqft` : '—')}
              </span>
            </div>

            <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80">
              <span className="text-slate-500 text-xs block">Transaction Type</span>
              <span className="font-semibold text-slate-200">{property.transaction || '—'}</span>
            </div>

            <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80">
              <span className="text-slate-500 text-xs block">Bathrooms</span>
              <span className="font-semibold text-slate-200">{property.bathroom}</span>
            </div>

            <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80">
              <span className="text-slate-500 text-xs block">Balconies</span>
              <span className="font-semibold text-slate-200">{property.balcony ?? '—'}</span>
            </div>

            <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80">
              <span className="text-slate-500 text-xs block">Parking Spaces</span>
              <span className="font-semibold text-slate-200">{property.parking_count ?? '—'}</span>
            </div>

            <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80">
              <span className="text-slate-500 text-xs block">Floor / Height</span>
              <span className="font-semibold text-slate-200">
                {property.floor_number ?? '—'} / {property.building_height ?? '—'}
              </span>
            </div>

            <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80">
              <span className="text-slate-500 text-xs block">Furnishing</span>
              <span className="font-semibold text-slate-200">{property.furnishing || 'Not Specified'}</span>
            </div>

            <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80">
              <span className="text-slate-500 text-xs block">Ownership</span>
              <span className="font-semibold text-slate-200">{property.ownership || 'Not Specified'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
        <button
          type="button"
          onClick={() => navigate('/')}
          className="w-full sm:w-auto px-8 py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl shadow-lg shadow-indigo-500/25 transition text-sm flex items-center justify-center gap-2"
        >
          <span>🔄</span> Calculate Another Property
        </button>
      </div>
    </div>
  );
};
