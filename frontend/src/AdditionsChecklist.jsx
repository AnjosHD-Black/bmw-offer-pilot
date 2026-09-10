import React, { useState, useEffect } from 'react';
import { Check, AlertCircle } from 'lucide-react';

export default function AdditionsChecklist({ backendUrl, onAdditionsChange }) {
  const [options, setOptions] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Lade verfügbare Optionen vom Backend
  useEffect(() => {
    fetchAdditionsOptions();
  }, [backendUrl]);

  const fetchAdditionsOptions = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${backendUrl}/additions-options`);
      if (!response.ok) throw new Error('Failed to fetch additions options');
      
      const data = await response.json();
      setOptions(data.options || []);
      setError(null);
    } catch (err) {
      setError(err.message);
      setOptions([]);
    } finally {
      setLoading(false);
    }
  };

  // Wenn Auswahl ändert, benachrichtige Parent-Component
  useEffect(() => {
    const selectedOptions = options.filter(opt => selected.has(opt.code));
    onAdditionsChange(selectedOptions);
  }, [selected, options, onAdditionsChange]);

  const toggleOption = (code) => {
    const newSelected = new Set(selected);
    if (newSelected.has(code)) {
      newSelected.delete(code);
    } else {
      newSelected.add(code);
    }
    setSelected(newSelected);
  };

  if (loading) return <div className="p-4 text-gray-500">Lade Optionen...</div>;

  return (
    <div className="p-0">
      <h3 className="text-xs font-semibold text-slate-300 mb-6 flex items-center gap-2 uppercase tracking-[0.28em]">
        <Check className="w-4 h-4 text-slate-400" />
        Zusätzliche Optionen
      </h3>

      {error && (
        <div className="text-red-500 mb-4 flex items-center gap-2 text-sm">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {options.length === 0 ? (
        <p className="text-slate-400 text-sm">Keine Optionen verfügbar</p>
      ) : (
        <div className="space-y-1">
          {options.map(option => (
            <label key={option.code} className="flex items-center gap-3 p-3 hover:bg-slate-700/30 rounded-lg cursor-pointer transition-colors">
              <input
                type="checkbox"
                checked={selected.has(option.code)}
                onChange={() => toggleOption(option.code)}
                className="w-4 h-4 accent-slate-500 border border-slate-600"
              />
              <div className="flex-1">
                <div className="font-medium text-slate-200 text-sm">{option.label}</div>
                <div className="text-xs text-slate-500">Code: {option.code}</div>
              </div>
              <div className="text-right">
                <div className="font-semibold text-slate-300 text-sm">€{option.price.toFixed(2)}</div>
              </div>
            </label>
          ))}
        </div>
      )}
      
      {selected.size > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-700/40">
          <p className="text-xs text-slate-400">
            <strong className="text-slate-300">{selected.size}</strong> Option{selected.size !== 1 ? 'en' : ''} ausgewählt
          </p>
        </div>
      )}
    </div>
  );
}
