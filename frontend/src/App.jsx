import React, { useState, useMemo, useCallback } from 'react';
// Icon-Importe
import { 
  Calendar, Code, Check, Truck, 
  X, BookOpen, Send, Zap, FileText, Download, User,
  Globe, Briefcase, Hash, Info, FileDown
} from 'lucide-react'; 

// --- KONSTANTEN & STRUKTUREN ---
// **********************************************

// Diese Listen bleiben erhalten, da sie die Dropdowns füllen
const DEPARTMENTS = ["MH", "FR", "CG", "JR"];
const NUMBER_TYPES = ["VIN", "Order NR.", "Proforma Order NR."];
const PRICE_TYPES_NET = ["NET VEHICLE PRICE", "NET VEHICLE PRICE WHS"];
const PRICE_TYPES_TOTAL = ["TOTAL OFFER PRICE", "TOTAL OFFER PRICE WHS", "TOTAL OFFER PRICE WHS GVT."];

const COUNTRIES = [
  "Abu Dhabi", "Egypt", "Australia", "Germany", "France", "Great Britain", 
  "USA", "China", "Dubai", "Switzerland", "Austria", "Sweden", "Norway"
];

// --- LEERE DATENBANKEN ---
// Hier kannst du später deine eigenen Beschreibungen und Preisregeln einfügen
const OPTION_DESCRIPTIONS = {}; 

const PRICING_DATABASE = {};

// Hilfsfunktion: Preis zum Datum finden (Gibt 0 zurück, da Datenbank leer ist)
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
  const [prodDate, setProdDate] = useState(new Date().toISOString().split('T')[0]);
  const [dept, setDept] = useState(DEPARTMENTS[0]);
  const [numType, setNumType] = useState(NUMBER_TYPES[0]);
  const [numValue, setNumValue] = useState("");
  const [country, setCountry] = useState(COUNTRIES[0]);
  const [priceTypeNet, setPriceTypeNet] = useState(PRICE_TYPES_NET[0]);
  const [priceTypeTotal, setPriceTypeTotal] = useState(PRICE_TYPES_TOTAL[0]);
  
  const [bulkCodes, setBulkCodes] = useState(''); // Jetzt leer
  const [extraNotes, setExtraNotes] = useState(''); // XXXL Feld, jetzt leer

  // Verkäufer-Stammdaten (Platzhalter)
  const salesPerson = { name: "Max Mustermann", id: "ADMIN-01" };

  // --- KALKULATION (für Export) ---
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
  const handleExport = (format) => {
    const formatCurrency = (val) => new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(val);
    
    let content = `BMW ANGEBOTSPROTOKOLL - DATENAUFNAHME\n`;
    content += `==========================================\n`;
    content += `PROD-DATUM: ${prodDate} | DEPT: ${dept}\n`;
    content += `${numType}: ${numValue || 'N/A'} | LAND: ${country}\n`;
    content += `PREIS-MODUS: ${priceTypeNet} / ${priceTypeTotal}\n`;
    content += `VERKÄUFER: ${salesPerson.name}\n\n`;
    content += `EINGEGEBENE OPTIONEN:\n`;
    
    if (calculation.allItems.length === 0) {
      content += `Keine Optionen eingegeben.\n`;
    } else {
      calculation.allItems.forEach(item => {
        content += `[${item.code}] ${item.name.padEnd(35)} | ${formatCurrency(item.price)}\n`;
      });
    }
    
    content += `\n------------------------------------------\n`;
    content += `GESAMTSUMME: ${formatCurrency(calculation.total)}\n\n`;
    content += `ZUSÄTZLICHE ANMERKUNGEN (XXXL):\n${extraNotes || 'Keine'}\n`;

    const mimeType = format === 'xlsx' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : 'application/pdf';
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `BMW_Export_${numValue || 'Data'}_${prodDate}.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="min-h-screen bg-slate-100 font-sans p-4 md:p-8">
      <div className="max-w-[1400px] mx-auto">
        
        {/* Header */}
        <header className="flex flex-col md:flex-row justify-between items-end mb-10 border-b-4 border-black pb-6">
          <div className="flex items-center space-x-6">
            <div className="w-20 h-20 bg-white border-4 border-slate-200 rounded-full flex items-center justify-center shadow-lg">
                <div className="w-14 h-14 bg-blue-700 rounded-full flex items-center justify-center text-white font-black text-[10px] border-4 border-white shadow-inner">BMW</div>
            </div>
            <div>
              <h1 className="text-5xl font-black tracking-tighter text-slate-900 uppercase italic leading-none">Order Entry</h1>
              <p className="text-slate-500 font-black tracking-widest text-sm uppercase mt-1">Empty Specification Template v5.0</p>
            </div>
          </div>
          <div className="text-right hidden md:block">
            <p className="text-xs font-black text-slate-400 uppercase">System Active</p>
            <p className="text-lg font-black text-slate-800">{salesPerson.name}</p>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
          
          {/* LINKES FELD: Formular */}
          <div className="lg:col-span-9 space-y-8">
            
            {/* Sektion 1: Stammdaten */}
            <div className="bg-white p-8 rounded-3xl shadow-2xl border border-slate-200">
              <h2 className="text-xs font-black uppercase tracking-[0.3em] text-blue-600 mb-8 flex items-center">
                <Briefcase className="mr-3" size={18} /> 01. Basis-Spezifikationen
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div>
                  <label className="block text-[10px] font-black text-slate-500 uppercase mb-2 tracking-widest">Produktionsdatum</label>
                  <div className="relative">
                    <Calendar className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                    <input type="date" value={prodDate} onChange={(e) => setProdDate(e.target.value)} className="w-full pl-12 pr-4 py-3 bg-slate-50 border-2 border-slate-100 rounded-2xl font-bold text-slate-700 focus:border-blue-500 focus:bg-white transition-all outline-none" />
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] font-black text-slate-500 uppercase mb-2 tracking-widest">Department</label>
                  <select value={dept} onChange={(e) => setDept(e.target.value)} className="w-full px-4 py-3 bg-slate-50 border-2 border-slate-100 rounded-2xl font-bold text-slate-700 focus:border-blue-500 focus:bg-white transition-all outline-none appearance-none">
                    {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-black text-slate-500 uppercase mb-2 tracking-widest">Ziel-Land</label>
                  <div className="relative">
                    <Globe className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                    <select value={country} onChange={(e) => setCountry(e.target.value)} className="w-full pl-12 pr-4 py-3 bg-slate-50 border-2 border-slate-100 rounded-2xl font-bold text-slate-700 focus:border-blue-500 focus:bg-white transition-all outline-none appearance-none">
                      {COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                </div>
              </div>

              {/* Identifikation */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-8 pt-8 border-t border-slate-100">
                <div>
                  <label className="block text-[10px] font-black text-slate-500 uppercase mb-2 tracking-widest">Art der Nummer</label>
                  <select value={numType} onChange={(e) => setNumType(e.target.value)} className="w-full px-4 py-3 bg-slate-50 border-2 border-slate-100 rounded-2xl font-bold text-slate-700 focus:border-blue-500 focus:bg-white transition-all outline-none">
                    {NUMBER_TYPES.map(n => <option key={n} value={n}>{n}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-black text-slate-500 uppercase mb-2 tracking-widest">Nummer (max. 10 Stellen)</label>
                  <div className="relative">
                    <Hash className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                    <input 
                      type="text" 
                      maxLength={10} 
                      value={numValue} 
                      onChange={(e) => setNumValue(e.target.value.toUpperCase())} 
                      placeholder="Ident-No."
                      className="w-full pl-12 pr-4 py-3 bg-slate-50 border-2 border-slate-100 rounded-2xl font-mono font-black text-slate-800 focus:border-blue-500 focus:bg-white transition-all outline-none" 
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Sektion 2: Bulk Input (Kompakt) */}
            <div className="bg-white p-8 rounded-3xl shadow-2xl border border-slate-200">
              <h2 className="text-xs font-black uppercase tracking-[0.3em] text-blue-600 mb-6 flex items-center">
                <Code size={20} className="mr-3" /> 02. Options-Codes Bulk Input
              </h2>
              <textarea 
                rows="5"
                value={bulkCodes}
                onChange={(e) => setBulkCodes(e.target.value)}
                placeholder="Codes hier einfügen (z.B. 1AB 2TC)..."
                className="w-full bg-slate-900 border-none rounded-2xl p-6 font-mono font-bold text-lg text-blue-400 shadow-inner focus:ring-4 focus:ring-blue-500/30 transition-all outline-none"
              ></textarea>
            </div>

            {/* Sektion 3: Extra Notes (JETZT XXXL) */}
            <div className="bg-white p-8 rounded-3xl shadow-2xl border border-slate-200">
              <div className="flex items-center justify-between mb-6">
                <label className="text-xs font-black uppercase tracking-[0.3em] text-orange-500 flex items-center">
                  <Info size={20} className="mr-3" /> 03. Zusätzliche technische Hinweise (XXXL)
                </label>
                <span className="text-[10px] bg-orange-100 text-orange-600 px-3 py-1 rounded-full font-black uppercase tracking-widest">Max Buffer</span>
              </div>
              
              <textarea 
                rows="40"
                value={extraNotes}
                onChange={(e) => setExtraNotes(e.target.value)}
                placeholder="Hier hunderte Zeilen technische Daten einfügen..."
                className="w-full bg-slate-50 border-2 border-slate-100 rounded-[2.5rem] p-8 font-mono text-xs text-slate-600 focus:bg-white transition-all outline-none focus:border-orange-400 leading-relaxed shadow-inner"
              ></textarea>
            </div>
          </div>

          {/* RECHTES FELD: Export Sidecenter */}
          <div className="lg:col-span-3 space-y-8">
            
            <div className="bg-slate-900 p-8 rounded-3xl shadow-2xl text-white border-b-8 border-blue-700 sticky top-8">
               <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] mb-6">Config & Export</h3>
               
               <div className="space-y-6 mb-10">
                  <div>
                    <label className="block text-[9px] font-black text-slate-400 uppercase mb-2 tracking-widest">Net Mode</label>
                    <select value={priceTypeNet} onChange={(e) => setPriceTypeNet(e.target.value)} className="w-full bg-slate-800 border-2 border-slate-700 rounded-xl p-3 text-xs font-black focus:border-blue-500 outline-none appearance-none">
                      {PRICE_TYPES_NET.map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-[9px] font-black text-slate-400 uppercase mb-2 tracking-widest">Total Mode</label>
                    <select value={priceTypeTotal} onChange={(e) => setPriceTypeTotal(e.target.value)} className="w-full bg-slate-800 border-2 border-slate-700 rounded-xl p-3 text-xs font-black focus:border-blue-500 outline-none appearance-none">
                      {PRICE_TYPES_TOTAL.map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                  </div>
               </div>

               <div className="flex flex-col space-y-4">
                  <button 
                    onClick={() => handleExport('pdf')} 
                    className="group w-full flex items-center justify-between bg-white text-slate-900 p-5 rounded-2xl hover:bg-slate-100 transition-all shadow-lg font-black text-xs uppercase tracking-widest"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="bg-red-500 text-white p-2 rounded-lg"><Download size={18} /></div>
                      <span>PDF Export</span>
                    </div>
                  </button>

                  <button 
                    onClick={() => handleExport('xlsx')} 
                    className="group w-full flex items-center justify-between bg-green-600 text-white p-5 rounded-2xl hover:bg-green-700 transition-all shadow-lg font-black text-xs uppercase tracking-widest"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="bg-white/20 p-2 rounded-lg"><FileText size={18} /></div>
                      <span>Excel Export</span>
                    </div>
                  </button>
               </div>

               <div className="mt-8 pt-8 border-t border-slate-800">
                  <div className="bg-slate-800 p-4 rounded-xl">
                      <p className="text-[9px] font-black text-slate-500 uppercase mb-2">System Ready</p>
                      <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                          <span className="text-[10px] font-bold text-slate-300">Clean Interface Active</span>
                      </div>
                  </div>
               </div>
            </div>
          </div>

        </div>

        {/* Footer */}
        <footer className="mt-20 text-center border-t-2 border-slate-200 pt-10 pb-20">
          <p className="text-[10px] text-slate-400 font-black uppercase tracking-[0.4em] italic">
            BMW Group Confidential | Technical Order Capture | {new Date().getFullYear()}
          </p>
        </footer>
      </div>
    </div>
  );
}