import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPrediction } from '../api/predictionClient';
import { PredictionRequest } from '../types/prediction';

const POPULAR_LOCATIONS = [
  'agra', 'ahmadnagar', 'ahmedabad', 'allahabad', 'aurangabad', 'badlapur',
  'bangalore', 'belgaum', 'bhiwadi', 'bhiwandi', 'bhopal', 'bhubaneswar',
  'chandigarh', 'chennai', 'coimbatore', 'dehradun', 'durgapur', 'ernakulam',
  'faridabad', 'ghaziabad', 'goa', 'greater-noida', 'guntur', 'gurgaon',
  'guwahati', 'gwalior', 'haridwar', 'hyderabad', 'indore', 'jabalpur',
  'jaipur', 'jamshedpur', 'jodhpur', 'kalyan', 'kanpur', 'kochi', 'kolkata',
  'kozhikode', 'lucknow', 'ludhiana', 'madurai', 'mangalore', 'mohali',
  'mumbai', 'mysore', 'nagpur', 'nashik', 'navi-mumbai', 'navsari', 'nellore',
  'new-delhi', 'noida', 'palakkad', 'palghar', 'panchkula', 'patna',
  'pondicherry', 'pune', 'raipur', 'rajahmundry', 'ranchi', 'satara', 'shimla',
  'siliguri', 'solapur', 'sonipat', 'surat', 'thane', 'thrissur', 'tirupati',
  'trichy', 'trivandrum', 'udaipur', 'udupi', 'vadodara', 'vapi', 'varanasi',
  'vijayawada', 'visakhapatnam', 'vrindavan', 'zirakpur',
];

export const PredictionForm: React.FC = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    location: '',
    locality: '',
    location_raw: '',
    transaction: 'Resale',
    furnishing: '',
    facing: '',
    overlooking: '',
    ownership: '',
    carpet_area: '',
    super_area: '',
    bathroom: 2,
    balcony: 1,
    parking_count: 1,
    floor_number: '',
    building_height: '',
  });

  const [citySearch, setCitySearch] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auto-calculated floor ratio
  const floorRatio = useMemo(() => {
    const fn = parseFloat(formData.floor_number);
    const bh = parseFloat(formData.building_height);
    if (!isNaN(fn) && !isNaN(bh) && bh > 0) {
      return (fn / bh).toFixed(3);
    }
    return null;
  }, [formData.floor_number, formData.building_height]);

  const filteredLocations = useMemo(() => {
    if (!citySearch) return [];
    return POPULAR_LOCATIONS.filter((l) =>
      l.toLowerCase().includes(citySearch.toLowerCase())
    ).slice(0, 10);
  }, [citySearch]);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleStepper = (
    field: 'bathroom' | 'balcony' | 'parking_count',
    delta: number,
    min = 0,
    max = 10
  ) => {
    setFormData((prev) => {
      const current = typeof prev[field] === 'number' ? prev[field] : 0;
      const next = Math.min(Math.max(current + delta, min), max);
      return { ...prev, [field]: next };
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.location) {
      setError('Please select or specify a valid city name.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: PredictionRequest = {
      location: formData.location.trim().toLowerCase(),
      locality: formData.locality.trim() || null,
      location_raw: formData.location_raw.trim() || null,
      transaction: formData.transaction,
      furnishing: formData.furnishing || null,
      facing: formData.facing || null,
      overlooking: formData.overlooking || null,
      ownership: formData.ownership || null,
      carpet_area: formData.carpet_area ? parseFloat(formData.carpet_area) : null,
      super_area: formData.super_area ? parseFloat(formData.super_area) : null,
      bathroom: parseFloat(formData.bathroom.toString()) || 1,
      balcony: formData.balcony !== '' ? parseFloat(formData.balcony.toString()) : null,
      parking_count: formData.parking_count !== '' ? parseFloat(formData.parking_count.toString()) : null,
      floor_number: formData.floor_number !== '' ? parseFloat(formData.floor_number) : null,
      building_height: formData.building_height !== '' ? parseFloat(formData.building_height) : null,
      floor_ratio: floorRatio ? parseFloat(floorRatio) : null,
    };

    try {
      const response = await getPrediction(payload);
      navigate('/result', {
        state: {
          prediction: response,
          property: payload,
        },
      });
    } catch (err: any) {
      setError(err.message || 'Failed to generate property price estimate.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-4xl mx-auto">
      {/* 1. Location Section */}
      <div className="bg-slate-900/80 border border-slate-800 backdrop-blur rounded-2xl p-6 sm:p-7 shadow-xl">
        <div className="flex items-center gap-3 mb-5">
          <span className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-lg">📍</span>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Location</h2>
            <p className="text-xs text-slate-400">City, neighborhood and locality</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="relative">
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              City <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              placeholder="e.g. mumbai, pune, bangalore"
              value={citySearch || formData.location}
              onChange={(e) => {
                setCitySearch(e.target.value);
                setFormData((prev) => ({ ...prev, location: e.target.value.toLowerCase() }));
                setDropdownOpen(true);
              }}
              onFocus={() => setDropdownOpen(true)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
            />

            {dropdownOpen && filteredLocations.length > 0 && (
              <div className="absolute z-20 top-full left-0 right-0 mt-1 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl overflow-hidden max-h-48 overflow-y-auto">
                {filteredLocations.map((loc) => (
                  <button
                    key={loc}
                    type="button"
                    onClick={() => {
                      setFormData((prev) => ({ ...prev, location: loc }));
                      setCitySearch(loc);
                      setDropdownOpen(false);
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-slate-300 hover:bg-indigo-600/20 hover:text-indigo-300 capitalize transition"
                  >
                    {loc}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Locality <span className="text-slate-500 text-[10px]">(optional)</span>
            </label>
            <input
              type="text"
              name="locality"
              placeholder="e.g. Andheri West"
              value={formData.locality}
              onChange={handleInputChange}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
            />
          </div>

          <div className="sm:col-span-2">
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Full Address / Society <span className="text-slate-500 text-[10px]">(optional)</span>
            </label>
            <input
              type="text"
              name="location_raw"
              placeholder="e.g. Lodha Palava, Dombivli East"
              value={formData.location_raw}
              onChange={handleInputChange}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
            />
          </div>
        </div>
      </div>

      {/* 2. Size Section */}
      <div className="bg-slate-900/80 border border-slate-800 backdrop-blur rounded-2xl p-6 sm:p-7 shadow-xl">
        <div className="flex items-center gap-3 mb-5">
          <span className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-lg">📐</span>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Size & Area</h2>
            <p className="text-xs text-slate-400">Dimensions in square feet</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Carpet Area <span className="text-slate-500 text-[10px]">(sqft)</span>
            </label>
            <div className="relative">
              <input
                type="number"
                name="carpet_area"
                min="0"
                placeholder="e.g. 850"
                value={formData.carpet_area}
                onChange={handleInputChange}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-3.5 pr-14 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
              />
              <span className="absolute right-3 top-2.5 text-xs font-mono text-slate-500">sqft</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Super / Built-up Area <span className="text-slate-500 text-[10px]">(sqft)</span>
            </label>
            <div className="relative">
              <input
                type="number"
                name="super_area"
                min="0"
                placeholder="e.g. 1100"
                value={formData.super_area}
                onChange={handleInputChange}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-3.5 pr-14 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
              />
              <span className="absolute right-3 top-2.5 text-xs font-mono text-slate-500">sqft</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Layout Section */}
      <div className="bg-slate-900/80 border border-slate-800 backdrop-blur rounded-2xl p-6 sm:p-7 shadow-xl">
        <div className="flex items-center gap-3 mb-5">
          <span className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-lg">🏠</span>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Layout & Amenities</h2>
            <p className="text-xs text-slate-400">Bathrooms, balconies & parking</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Bathrooms <span className="text-rose-500">*</span>
            </label>
            <div className="flex items-center border border-slate-800 rounded-xl overflow-hidden bg-slate-950">
              <button
                type="button"
                onClick={() => handleStepper('bathroom', -1, 1, 10)}
                className="px-3.5 py-2.5 bg-slate-900 hover:bg-indigo-600/20 text-indigo-400 font-bold transition"
              >
                −
              </button>
              <input
                type="number"
                name="bathroom"
                readOnly
                value={formData.bathroom}
                className="w-full text-center bg-transparent font-mono text-sm font-semibold text-slate-100 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => handleStepper('bathroom', 1, 1, 10)}
                className="px-3.5 py-2.5 bg-slate-900 hover:bg-indigo-600/20 text-indigo-400 font-bold transition"
              >
                +
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Balconies <span className="text-slate-500 text-[10px]">(optional)</span>
            </label>
            <div className="flex items-center border border-slate-800 rounded-xl overflow-hidden bg-slate-950">
              <button
                type="button"
                onClick={() => handleStepper('balcony', -1, 0, 10)}
                className="px-3.5 py-2.5 bg-slate-900 hover:bg-indigo-600/20 text-indigo-400 font-bold transition"
              >
                −
              </button>
              <input
                type="number"
                name="balcony"
                readOnly
                value={formData.balcony}
                className="w-full text-center bg-transparent font-mono text-sm font-semibold text-slate-100 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => handleStepper('balcony', 1, 0, 10)}
                className="px-3.5 py-2.5 bg-slate-900 hover:bg-indigo-600/20 text-indigo-400 font-bold transition"
              >
                +
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Parking Spaces <span className="text-slate-500 text-[10px]">(optional)</span>
            </label>
            <div className="flex items-center border border-slate-800 rounded-xl overflow-hidden bg-slate-950">
              <button
                type="button"
                onClick={() => handleStepper('parking_count', -1, 0, 10)}
                className="px-3.5 py-2.5 bg-slate-900 hover:bg-indigo-600/20 text-indigo-400 font-bold transition"
              >
                −
              </button>
              <input
                type="number"
                name="parking_count"
                readOnly
                value={formData.parking_count}
                className="w-full text-center bg-transparent font-mono text-sm font-semibold text-slate-100 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => handleStepper('parking_count', 1, 0, 10)}
                className="px-3.5 py-2.5 bg-slate-900 hover:bg-indigo-600/20 text-indigo-400 font-bold transition"
              >
                +
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Building Section */}
      <div className="bg-slate-900/80 border border-slate-800 backdrop-blur rounded-2xl p-6 sm:p-7 shadow-xl">
        <div className="flex items-center gap-3 mb-5">
          <span className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-lg">🏢</span>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Building Details</h2>
            <p className="text-xs text-slate-400">Floor level & height</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Floor Number <span className="text-slate-500 text-[10px]">(optional)</span>
            </label>
            <input
              type="number"
              name="floor_number"
              min="0"
              placeholder="e.g. 5"
              value={formData.floor_number}
              onChange={handleInputChange}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Total Floors <span className="text-slate-500 text-[10px]">(optional)</span>
            </label>
            <input
              type="number"
              name="building_height"
              min="1"
              placeholder="e.g. 20"
              value={formData.building_height}
              onChange={handleInputChange}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Floor Ratio <span className="text-slate-500 text-[10px]">(auto)</span>
            </label>
            <div className="flex items-center px-3.5 py-2.5 bg-slate-950 border border-dashed border-indigo-500/30 rounded-xl text-indigo-400 font-mono text-sm font-semibold">
              <span>= {floorRatio ?? '—'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 5. Property Details Section */}
      <div className="bg-slate-900/80 border border-slate-800 backdrop-blur rounded-2xl p-6 sm:p-7 shadow-xl">
        <div className="flex items-center gap-3 mb-5">
          <span className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-lg">🏷️</span>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Property Details</h2>
            <p className="text-xs text-slate-400">Transaction type, ownership & orientation</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Transaction Type <span className="text-rose-500">*</span>
            </label>
            <select
              name="transaction"
              value={formData.transaction}
              onChange={handleInputChange}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
            >
              <option value="Resale">Resale</option>
              <option value="New Property">New Property</option>
              <option value="Other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Furnishing <span className="text-slate-500 text-[10px]">(optional)</span>
            </label>
            <select
              name="furnishing"
              value={formData.furnishing}
              onChange={handleInputChange}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
            >
              <option value="">Not specified</option>
              <option value="Furnished">Furnished</option>
              <option value="Semi-Furnished">Semi-Furnished</option>
              <option value="Unfurnished">Unfurnished</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Facing <span className="text-slate-500 text-[10px]">(optional)</span>
            </label>
            <select
              name="facing"
              value={formData.facing}
              onChange={handleInputChange}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
            >
              <option value="">Not specified</option>
              <option value="East">East</option>
              <option value="West">West</option>
              <option value="North">North</option>
              <option value="South">South</option>
              <option value="North - East">North - East</option>
              <option value="North - West">North - West</option>
              <option value="South - East">South - East</option>
              <option value="South -West">South - West</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Ownership <span className="text-slate-500 text-[10px]">(optional)</span>
            </label>
            <select
              name="ownership"
              value={formData.ownership}
              onChange={handleInputChange}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
            >
              <option value="">Not specified</option>
              <option value="Freehold">Freehold</option>
              <option value="Co-operative Society">Co-operative Society</option>
              <option value="Leasehold">Leasehold</option>
              <option value="Power Of Attorney">Power Of Attorney</option>
            </select>
          </div>

          <div className="sm:col-span-2">
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Overlooking <span className="text-slate-500 text-[10px]">(optional)</span>
            </label>
            <select
              name="overlooking"
              value={formData.overlooking}
              onChange={handleInputChange}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
            >
              <option value="">Not specified</option>
              <option value="Garden/Park">Garden / Park</option>
              <option value="Main Road">Main Road</option>
              <option value="Pool">Pool</option>
              <option value="Garden/Park, Main Road">Garden / Park & Main Road</option>
              <option value="Garden/Park, Pool">Garden / Park & Pool</option>
              <option value="Main Road, Pool">Main Road & Pool</option>
              <option value="Garden/Park, Main Road, Pool">Garden / Park, Main Road & Pool</option>
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-center text-sm font-medium">
          {error}
        </div>
      )}

      {/* Submit Button */}
      <div className="text-center pt-2">
        <button
          type="submit"
          disabled={loading}
          className="w-full max-w-md mx-auto py-4 px-8 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-base shadow-lg shadow-indigo-500/25 transition transform active:scale-98 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
              </svg>
              Calculating Valuation...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Get Price Estimate
            </>
          )}
        </button>
      </div>
    </form>
  );
};
