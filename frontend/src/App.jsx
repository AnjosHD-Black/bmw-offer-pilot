import React, { useState, useMemo, useCallback } from 'react';
// Icon-Importe
import { 
  Calendar, Code, Check, Truck, 
  X, BookOpen, Send, Zap, FileText, Download, User,
  Globe, Briefcase, Hash, Info, FileDown, ChevronRight
} from 'lucide-react'; 

// --- KONSTANTEN & STRUKTUREN ---
// **********************************************

// Backend URL (wird von .env gelesen, fallback zu localhost)
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const DEPARTMENTS = ["MH", "FR", "CG", "JR"];
const NUMBER_TYPES = ["VIN", "Order NR.", "Proforma Order NR."];
const PRICE_TYPES_NET = ["NET VEHICLE PRICE", "NET VEHICLE PRICE WHS"];
const PRICE_TYPES_TOTAL = ["TOTAL OFFER PRICE", "TOTAL OFFER PRICE WHS", "TOTAL OFFER PRICE WHS GVT."];

const COUNTRIES = [
  "Abu Dhabi", "Egypt", "Australia", "Germany", "France", "Great Britain", 
  "USA", "China", "Dubai", "Switzerland", "Austria", "Sweden", "Norway"
];

// Leere Datenbanken für eigene Erweiterungen
const OPTION_DESCRIPTIONS = {}; 
const PRICING_DATABASE = {};

// Hilfsfunktion: Preis zum Datum finden
const getPriceByDate = (code, dateStr) => {
  const rules = PRICING_DATABASE[code];
  if (!rules) return 0;
  
  const targetDate = new Date(dateStr);
  const rule = rules.find(r => {
    const start = new Date(r.start);
    const end = new Date(r.end);
    return targetDate >= start && targetDate <= end;
  });
  
  return rule ? rule.price : (rules[0] ? rules[0].price : 0);
};

/** --- HAUPTKOMPONENTE --- **/

export default function App() {
  // --- STATES ---
  const today = new Date().toISOString().split('T')[0];
  const [prodDate, setProdDate] = useState(today);
  const [dept, setDept] = useState(DEPARTMENTS[0]);
  const [numType, setNumType] = useState(NUMBER_TYPES[0]);
  const [numValue, setNumValue] = useState("");
  const [country, setCountry] = useState(COUNTRIES[0]);
  const [priceTypeNet, setPriceTypeNet] = useState(PRICE_TYPES_NET[0]);
  const [priceTypeTotal, setPriceTypeTotal] = useState(PRICE_TYPES_TOTAL[0]);
  
  const [bulkCodes, setBulkCodes] = useState(''); 
  const [pricedCodes, setPricedCodes] = useState('');
  const [extraNotes, setExtraNotes] = useState(''); // XXXL Feld

  const salesPerson = { name: "Max Mustermann", id: "ADMIN-01" };

  // --- KALKULATION (für Export-Protokoll) ---
  const calculation = useMemo(() => {
    const parsedBulk = bulkCodes.split(/\s+/).filter(c => c.trim().length > 0);
    
    const allItems = parsedBulk.map(code => ({
        type: 'Option',
        code: code,
        name: OPTION_DESCRIPTIONS[code] || 'Zusatzausstattung',
        price: getPriceByDate(code, prodDate)
    }));

    const total = allItems.reduce((sum, item) => sum + item.price, 0);
    return { allItems, total };
  }, [prodDate, bulkCodes]);

  // --- EXPORT FUNKTION ---
// --- EXPORT FUNKTION (LIVE BACKEND) ---
const handleExport = async (format) => {
  try {
    const payload = {
      date: prodDate,
      model: bulkCodes.split(/\s+/)[0] || "",
      color: bulkCodes.split(/\s+/)[1] || "",
      interior: bulkCodes.split(/\s+/)[2] || "",
      all_codes: bulkCodes
        .split(/\s+/)
        .map(c => c.trim())
        .filter(Boolean),

      priced_lines: bulkCodes
        .split("\n")
        .map(l => l.trim())
        .filter(l => /\d+$/.test(l)),

      format: format === "xlsx" ? "excel" : "pdf"
    };

    const response = await fetch(`${BACKEND_URL}/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error("Backend error");
    }
    
    content += `\n------------------------------------------\n`;
    content += `GESAMTSUMME: ${formatCurrency(calculation.total)}\n\n`;
    
    content += `\nCODES MIT PREISEN:\n`;
    if (pricedCodes.trim()) {
      content += pricedCodes + '\n';
    } else {
      content += 'Keine Einträge\n';
    }
    
    content += `\nZUSÄTZLICHE ANMERKUNGEN (XXXL):\n${extraNotes || 'Keine'}\n`;

    const mimeType = format === 'xlsx' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : 'application/pdf';
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `BMW_Spec_Export_${numValue || 'Data'}_${prodDate}.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  } catch (error) {
    console.error('Export failed:', error);
    alert('Export fehlgeschlagen. Bitte versuchen Sie es erneut.');
  }
};

  return (
    <div className="min-h-screen bg-slate-100 font-sans pb-20">
      
      {/* Header Bereich */}
      <nav className="bg-white text-slate-900 h-16 shadow-sm border-b border-slate-200 flex items-center mb-8">
        <div className="max-w-[1400px] mx-auto w-full px-8 flex justify-between items-center">
          <div className="flex items-center space-x-4">
             <div className="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center text-white font-semibold text-[10px]">BMW</div>
             <div className="h-6 w-px bg-slate-200"></div>
             <span className="text-sm font-semibold text-slate-600">Order Capture v8.0</span>
          </div>
          <div className="hidden lg:flex items-center space-x-2 text-slate-600 text-sm">
            <User size={16} className="text-blue-600" />
            <span className="font-semibold">{salesPerson.name}</span>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-12 md:px-12 md:py-16">
        
        {/* Dynamic Title Area */}
        <header className="mb-10 animate-in slide-in-from-top-4 duration-700">
          <div className="flex items-center space-x-2 text-slate-600 mb-3 text-xs font-semibold">
            <span>BMW Group Dashboard</span>
            <ChevronRight size={14} className="text-slate-400" />
            <span className="text-slate-500">Specification Capture</span>
          </div>
          <h1 className="text-4xl font-semibold text-slate-900 leading-tight">
            Order Entry System
          </h1>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
          
          {/* LINKES FELD: Eingabe-Bereich */}
          <div className="lg:col-span-9 space-y-8">
            
            {/* Sektion 1: Stammdaten */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h2 className="text-sm font-semibold text-blue-600 mb-6 flex items-center">
                <Briefcase className="mr-2" size={18} />Basis-Spezifikationen
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-2">Produktionsdatum</label>
                  <input type="date" value={prodDate} onChange={(e) => setProdDate(e.target.value)} className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-700 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none" />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-2">Department</label>
                  <select value={dept} onChange={(e) => setDept(e.target.value)} className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-700 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none appearance-none">
                    {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-2">Ziel-Land</label>
                  <select value={country} onChange={(e) => setCountry(e.target.value)} className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-700 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none appearance-none">
                    {COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
              </div>

              {/* Identifikation */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6 pt-6 border-t border-slate-100">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-2">Art der Nummer</label>
                  <select value={numType} onChange={(e) => setNumType(e.target.value)} className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-700 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all">
                    {NUMBER_TYPES.map(n => <option key={n} value={n}>{n}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-2">Nummer (max. 10 Stellen)</label>
                  <div className="relative">
                    <Hash className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                    <input 
                      type="text" 
                      maxLength={10} 
                      value={numValue} 
                      onChange={(e) => setNumValue(e.target.value.toUpperCase())} 
                      placeholder="Ident-No."
                      className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-lg font-mono text-slate-700 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none" 
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Sektion 2: Bulk Input */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h2 className="text-sm font-semibold text-blue-600 mb-4 flex items-center">
                <Code size={16} className="mr-2" />Options-Codes Bulk Input
              </h2>
              <textarea 
                rows="5"
                value={bulkCodes}
                onChange={(e) => setBulkCodes(e.target.value)}
                placeholder="Codes hier einfügen (z.B. 1AB 2TC 3B3)..."
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-4 font-mono text-base text-slate-700 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none leading-relaxed"
              ></textarea>
            </div>

            {/* Sektion 2b: Priced Codes */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h2 className="text-sm font-semibold text-blue-600 mb-4 flex items-center">
                <Code size={16} className="mr-2" />Codes mit Preisen
              </h2>
              <textarea 
                rows="6"
                value={pricedCodes}
                onChange={(e) => setPricedCodes(e.target.value)}
                placeholder="Format: CODE Name Price (eine pro Zeile)&#10;1AB Brakes 500&#10;1AC Floor Mats 200&#10;109 Security Package VR6 1000"
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-4 font-mono text-base text-slate-700 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none leading-relaxed"
              ></textarea>
            </div>

            {/* Sektion 3: Extra Notes (XXXL) */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <div className="flex items-center justify-between mb-4">
                <label className="text-sm font-semibold text-slate-700 flex items-center">
                  Zusätzliche technische Hinweise (XXXL)
                </label>
                <span className="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded font-semibold">Large Buffer</span>
              </div>
              
              <textarea 
                rows="40"
                value={extraNotes}
                onChange={(e) => setExtraNotes(e.target.value)}
                placeholder="Hier hunderte Zeilen technische Daten einfügen..."
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-4 font-mono text-sm text-slate-600 focus:bg-white transition-all outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 leading-relaxed"
              ></textarea>
            </div>
          </div>

          {/* RECHTES FELD: Export Center */}
          <div className="lg:col-span-3 space-y-8">
            
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 sticky top-28">
               <h3 className="text-xs font-semibold text-slate-700 mb-5">Export Configuration</h3>
               
               <div className="space-y-5 mb-6">
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-2">Net Mode</label>
                    <select value={priceTypeNet} onChange={(e) => setPriceTypeNet(e.target.value)} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none appearance-none transition-all text-slate-700">
                      {PRICE_TYPES_NET.map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-2">Total Mode</label>
                    <select value={priceTypeTotal} onChange={(e) => setPriceTypeTotal(e.target.value)} className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none appearance-none transition-all text-slate-700">
                      {PRICE_TYPES_TOTAL.map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                  </div>
               </div>

               <div className="flex flex-col space-y-3">
                  <button 
                    onClick={() => handleExport('pdf')} 
                    className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-lg transition-all font-semibold text-sm"
                  >
                    <Download size={16} />
                    <span>PDF Protokoll</span>
                  </button>

                  <button 
                    onClick={() => handleExport('xlsx')} 
                    className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-lg transition-all font-semibold text-sm"
                  >
                    <FileText size={16} />
                    <span>Excel Export</span>
                  </button>
               </div>

               <div className="mt-6 pt-6 border-t border-slate-200">
                  <div className="bg-blue-50 p-3 rounded-lg">
                      <p className="text-xs font-semibold text-slate-700 mb-2">System Status</p>
                      <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                          <span className="text-xs text-slate-600">Ready</span>
                      </div>
                  </div>
               </div>
            </div>
          </div>

        </div>

        {/* Footer Area */}
        <footer className="mt-20 text-center border-t border-slate-200 pt-10 pb-20">
          <p className="text-xs text-slate-500 font-semibold">
            BMW Group Confidential | Technical Capture Environment | {new Date().getFullYear()}
          </p>
        </footer>
      </div>
    </div>
  );
}