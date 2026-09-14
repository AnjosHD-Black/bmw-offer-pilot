import React, { useState, useMemo, useCallback } from 'react';
import './App.css';
// Icon-Importe
import { 
  Calendar, Code, Check, Truck, 
  X, BookOpen, Send, Zap, FileText, Download, User,
  Globe, Briefcase, Hash, Info, FileDown, ChevronRight
} from 'lucide-react'; 

import AdditionsChecklist from './AdditionsChecklist'; 

// --- KONSTANTEN & STRUKTUREN ---
// **********************************************

// Backend URLs für G05 und G73
const BACKEND_URLS = {
  A: import.meta.env.VITE_BACKEND_URL_G05 || '/api/g05',  // G05
  B: import.meta.env.VITE_BACKEND_URL_G73 || '/api/g73'   // G73
};

const CONTRACT_BACKEND_URL = import.meta.env.VITE_CONTRACT_BACKEND_URL || '/api/contract';

const DEPARTMENTS = ["MH", "FR", "CG", "JR"];
const NUMBER_TYPES = ["VIN", "Order NR.", "Proforma Order NR."];
const PRICE_TYPES_NET = ["NET VEHICLE PRICE", "NET VEHICLE PRICE WHS"];
const PRICE_TYPES_TOTAL = ["TOTAL OFFER PRICE", "TOTAL OFFER PRICE WHS", "TOTAL OFFER PRICE WHS GVT."];

const COUNTRIES = [
  "Abu Dhabi", "Egypt", "Australia", "Germany", "France", "Great Britain", 
  "USA", "China", "Dubai", "Switzerland", "Austria", "Sweden", "Norway"
];

const CONTRACT_SELLERS = ["CS-201 MH", "CS-201 DW", "CS-201 MM"];
const SPECIAL_EQUIPMENT_OPTIONS = ["10C", "10G", "10L", "10M", "10P", "940"];

const extractValidCodes = (value) =>
  value
    .split(/\s+/)
    .map(code => code.trim().toUpperCase())
    .filter(code => /^[A-Z0-9]{3,4}$/.test(code));

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
  const createCarState = () => ({
    prodDate: today,
    dept: DEPARTMENTS[0],
    numType: NUMBER_TYPES[0],
    numValue: "",
    country: COUNTRIES[0],
    priceTypeNet: PRICE_TYPES_NET[0],
    priceTypeTotal: PRICE_TYPES_TOTAL[0],
    bulkCodes: "",
    pricedCodes: "",
    extraNotes: "",
    additions: [], // Array von ausgewählten Additions-Optionen
  });

  const [activeCar, setActiveCar] = useState("A");
  const [carA, setCarA] = useState(createCarState);
  const [carB, setCarB] = useState(createCarState);
  const [contractState, setContractState] = useState({
    contractSeries: "G05",
    sellerCode: CONTRACT_SELLERS[0],
    buyerFirstName: "",
    buyerSurname: "",
    buyerStreet: "",
    buyerCity: "",
    buyerPostalCode: "",
    buyerCountry: "",
    buyerVat: "",
    buyerTaxNo: "",
    buyerPhone: "",
    buyerEmail: "",
    buyerRepresentedBy: "",
    quantity: "1",
    price: "",
    vin: "",
    orderNumber: "",
    specialEquipment: []
  });

  const activeCarState = activeCar === "B" ? carB : carA;
  const setActiveCarState = activeCar === "B" ? setCarB : setCarA;
  const isContractMode = activeCar === "CONTRACT";

  const salesPerson = { name: "Max Mustermann", id: "ADMIN-01" };

  // --- ADDITIONS HANDLER ---
  const handleAdditionsChange = useCallback((selectedAdditions) => {
    setActiveCarState(prev => ({
      ...prev,
      additions: selectedAdditions
    }));
  }, [setActiveCarState]);

  // --- KALKULATION (für Export-Protokoll) ---
  const calculation = useMemo(() => {
    const parsedBulk = extractValidCodes(activeCarState.bulkCodes);

    const allItems = parsedBulk.map(code => ({
      type: 'Option',
      code: code,
      name: OPTION_DESCRIPTIONS[code] || 'Zusatzausstattung',
      price: getPriceByDate(code, activeCarState.prodDate)
    }));

    const total = allItems.reduce((sum, item) => sum + item.price, 0);
    return { allItems, total };
  }, [activeCarState]);

  // --- EXPORT FUNKTION (LIVE BACKEND) ---
const handleExport = async (format, carState, carId) => {
  try {
    // Get the correct backend URL based on the car ID
    const backendUrl = BACKEND_URLS[carId] || BACKEND_URLS.A;
    
    // Filter für nur 3-4 stellige alphanumerische Codes
    const validCodes = extractValidCodes(carState.bulkCodes);
    
    // Verwandle Additions zu pricedLines Format
    const additionLines = carState.additions
      .map(add => `${add.code} ${add.label} ${add.price.toFixed(2)}`)
      .join('\n');
    
    // Vereinige priced_codes mit additions
    const allPricedLines = carState.pricedCodes + (carState.additions.length > 0 ? '\n' + additionLines : '');
    
    const payload = {
      date: carState.prodDate,
      model: "",
      color: "",
      interior: "",
      all_codes: validCodes,

      priced_lines: allPricedLines
        .split("\n")
        .map(l => l.trim())
        .filter(Boolean),

      format: format === "xlsx" ? "excel" : "pdf"
    };

    const response = await fetch(`${backendUrl}/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Backend error:', errorData);
      throw new Error(`Backend error: ${response.status}`);
    }
    
    // Hole die Datei als Blob
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `BMW_Spec_Export_${carState.numValue || 'Data'}_${carState.prodDate}.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Export failed:', error);
    alert('Export fehlgeschlagen. Bitte versuchen Sie es erneut.');
  }
};

const handleContractExport = async () => {
  try {
    const payload = {
      contract_series: contractState.contractSeries,
      seller_code: contractState.sellerCode,
      buyer_first_name: contractState.buyerFirstName,
      buyer_surname: contractState.buyerSurname,
      buyer_street: contractState.buyerStreet,
      buyer_city: contractState.buyerCity,
      buyer_postal_code: contractState.buyerPostalCode,
      buyer_country: contractState.buyerCountry,
      buyer_vat: contractState.buyerVat,
      buyer_tax_no: contractState.buyerTaxNo,
      buyer_phone: contractState.buyerPhone,
      buyer_email: contractState.buyerEmail,
      buyer_represented_by: contractState.buyerRepresentedBy,
      quantity: contractState.quantity,
      price: contractState.price,
      vin: contractState.vin,
      order_number: contractState.orderNumber,
      special_equipment: contractState.specialEquipment
    };

    const response = await fetch(`${CONTRACT_BACKEND_URL}/generate-contract`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Contract backend error:', errorData);
      throw new Error(`Contract backend error: ${response.status}`);
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `BMW_Vertrag_${contractState.orderNumber || 'DRAFT'}.docx`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Contract export failed:', error);
    alert('Vertragsexport fehlgeschlagen. Bitte versuchen Sie es erneut.');
  }
};

const toggleSpecialEquipment = (code) => {
  setContractState(prev => ({
    ...prev,
    specialEquipment: prev.specialEquipment.includes(code)
      ? prev.specialEquipment.filter(item => item !== code)
      : [...prev.specialEquipment, code]
  }));
};

const handleExcelImport = async (file) => {
  if (!file) return;

  const backendUrl = BACKEND_URLS[activeCar] || BACKEND_URLS.A;
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(`${backendUrl}/upload-excel-options`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Excel-Import fehlgeschlagen');
    }

    const data = await response.json();
    setActiveCarState(prev => ({
      ...prev,
      bulkCodes: data.all_codes.join(' '),
      pricedCodes: data.priced_lines.join('\n'),
    }));

    alert('Excel-Datei erfolgreich importiert.');
  } catch (error) {
    console.error('Excel upload failed:', error);
    alert(error.message || 'Excel konnte nicht importiert werden.');
  }
};

  return (
    <div className={`app-shell ${
      isContractMode ? '' : activeCar === 'A' ? 'app-shell--g05' : 'app-shell--g73'
    }`}>
      
      {/* Header Bereich */}
      <nav className="top-bar">
        <div className="max-w-[1400px] mx-auto w-full px-4 sm:px-6 lg:px-8 py-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
             <div className="brand-mark">BMW</div>
             <div>
              <div className="text-xs uppercase tracking-[0.3em] text-slate-400 font-semibold">BMW Group</div>
              <span className="text-sm font-semibold text-slate-200">Quotation Builder</span>
             </div>
          </div>
          <div className="hidden sm:flex items-center gap-2 text-slate-300 text-sm status-chip">
            <User size={16} className="text-blue-600" />
            <span className="font-semibold">{salesPerson.name}</span>
          </div>
        </div>
      </nav>

      <div className="max-w-[1440px] mx-auto px-4 py-8 sm:px-6 md:px-8 lg:px-10 lg:py-10">
        
        {/* Dynamic Title Area */}
        <header className="hero-card hero-card--compact mb-14 animate-in slide-in-from-top-4 duration-700">
          <div className="flex items-center justify-between flex-wrap gap-4 mb-4">
            <div className="flex items-center flex-wrap gap-2 text-slate-300 text-xs font-semibold uppercase tracking-[0.24em]">
              <span className="pill">BMW Group Dashboard</span>
              <ChevronRight size={14} className="text-slate-500" />
              <span className="text-slate-400">
                {isContractMode
                  ? 'Contract Builder'
                  : activeCar === 'B'
                    ? 'Quotation G73'
                    : 'Quotation G05'}
              </span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1 bg-slate-700/40 rounded-full">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-slate-200 font-semibold">Ready</span>
            </div>
          </div>
          <div>
            <h1 className="display-title text-4xl md:text-5xl font-semibold text-slate-50 leading-tight">
              {isContractMode
                ? 'Contract Generation'
                : activeCar === 'B'
                  ? 'Quotation G73'
                  : 'Quotation G05'}
            </h1>
          </div>
        </header>

        <div className="tab-group mb-8">
          <button
            type="button"
            onClick={() => setActiveCar("A")}
            className={`tab-button ${
              activeCar === "A" ? "tab-button--active" : ""
            }`}
          >
            G05
          </button>
          <button
            type="button"
            onClick={() => setActiveCar("B")}
            className={`tab-button ${
              activeCar === "B" ? "tab-button--active" : ""
            }`}
          >
            G73
          </button>
          <button
            type="button"
            onClick={() => setActiveCar("CONTRACT")}
            className={`tab-button ${
              activeCar === "CONTRACT" ? "tab-button--active" : ""
            }`}
          >
            Vertrag
          </button>
        </div>

        {isContractMode ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-14 stagger">
            <div className="lg:col-span-9 flex flex-col gap-5">
              <div className="panel p-8 stagger-item">
                <h2 className="section-title mb-6">
                  <BookOpen className="mr-2" size={18} />Vertragsdaten
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div>
                    <label className="field-label">Baureihe</label>
                    <select
                      value={contractState.contractSeries}
                      onChange={(e) => setContractState(prev => ({ ...prev, contractSeries: e.target.value }))}
                      className="field"
                    >
                      <option value="G05">G05</option>
                      <option value="G73">G73</option>
                    </select>
                  </div>

                  <div>
                    <label className="field-label">Verkäufer</label>
                    <select
                      value={contractState.sellerCode}
                      onChange={(e) => setContractState(prev => ({ ...prev, sellerCode: e.target.value }))}
                      className="field"
                    >
                      {CONTRACT_SELLERS.map((seller) => (
                        <option key={seller} value={seller}>{seller}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="mt-10 pt-8 border-t border-slate-700/60">
                  <h3 className="text-sm font-semibold text-slate-100 mb-6">Buyer</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div>
                      <label className="field-label">Firstname</label>
                      <input
                        type="text"
                        value={contractState.buyerFirstName}
                        onChange={(e) => setContractState(prev => ({ ...prev, buyerFirstName: e.target.value }))}
                        className="field"
                      />
                    </div>

                    <div>
                      <label className="field-label">Surname</label>
                      <input
                        type="text"
                        value={contractState.buyerSurname}
                        onChange={(e) => setContractState(prev => ({ ...prev, buyerSurname: e.target.value }))}
                        className="field"
                      />
                    </div>

                    <div className="md:col-span-2">
                      <label className="field-label">Straße mit Hausnummer</label>
                      <input
                        type="text"
                        value={contractState.buyerStreet}
                        onChange={(e) => setContractState(prev => ({ ...prev, buyerStreet: e.target.value }))}
                        className="field"
                      />
                    </div>

                    <div>
                      <label className="field-label">Stadt</label>
                      <input
                        type="text"
                        value={contractState.buyerCity}
                        onChange={(e) => setContractState(prev => ({ ...prev, buyerCity: e.target.value }))}
                        className="field"
                      />
                    </div>

                    <div>
                      <label className="field-label">Postleitzahl</label>
                      <input
                        type="text"
                        value={contractState.buyerPostalCode}
                        onChange={(e) => setContractState(prev => ({ ...prev, buyerPostalCode: e.target.value }))}
                        className="field"
                      />
                    </div>

                    <div>
                      <label className="field-label">Country</label>
                      <input
                        type="text"
                        value={contractState.buyerCountry}
                        onChange={(e) => setContractState(prev => ({ ...prev, buyerCountry: e.target.value }))}
                        className="field"
                      />
                    </div>

                    <div>
                      <label className="field-label">VAT</label>
                      <input
                        type="text"
                        value={contractState.buyerVat}
                        onChange={(e) => setContractState(prev => ({ ...prev, buyerVat: e.target.value }))}
                        className="field"
                      />
                    </div>

                    <div>
                      <label className="field-label">Tax No.</label>
                      <input
                        type="text"
                        value={contractState.buyerTaxNo}
                        onChange={(e) => setContractState(prev => ({ ...prev, buyerTaxNo: e.target.value }))}
                        className="field"
                      />
                    </div>

                    <div>
                      <label className="field-label">Phone</label>
                      <input
                        type="text"
                        value={contractState.buyerPhone}
                        onChange={(e) => setContractState(prev => ({ ...prev, buyerPhone: e.target.value }))}
                        className="field"
                      />
                    </div>

                    <div>
                      <label className="field-label">Mail</label>
                      <input
                        type="email"
                        value={contractState.buyerEmail}
                        onChange={(e) => setContractState(prev => ({ ...prev, buyerEmail: e.target.value }))}
                        className="field"
                      />
                    </div>

                    <div className="md:col-span-2">
                      <label className="field-label">Represented by</label>
                      <input
                        type="text"
                        value={contractState.buyerRepresentedBy}
                        onChange={(e) => setContractState(prev => ({ ...prev, buyerRepresentedBy: e.target.value }))}
                        className="field"
                      />
                    </div>
                  </div>
                </div>

                <div className="mt-10 pt-8 border-t border-slate-700/60">
                  <h3 className="text-sm font-semibold text-slate-100 mb-6">Infos übers Auto</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div>
                      <label className="field-label">Quantity</label>
                      <input
                        type="number"
                        min="1"
                        value={contractState.quantity}
                        onChange={(e) => setContractState(prev => ({ ...prev, quantity: e.target.value }))}
                        className="field"
                      />
                    </div>

                    <div>
                      <label className="field-label">Price</label>
                      <input
                        type="text"
                        value={contractState.price}
                        onChange={(e) => setContractState(prev => ({ ...prev, price: e.target.value }))}
                        className="field"
                      />
                    </div>

                    <div>
                      <label className="field-label">VIN 17</label>
                      <input
                        type="text"
                        maxLength={17}
                        value={contractState.vin}
                        onChange={(e) => setContractState(prev => ({ ...prev, vin: e.target.value.toUpperCase() }))}
                        className="field"
                      />
                    </div>

                    <div>
                      <label className="field-label">Order Nummer</label>
                      <input
                        type="text"
                        value={contractState.orderNumber}
                        onChange={(e) => setContractState(prev => ({ ...prev, orderNumber: e.target.value.toUpperCase() }))}
                        className="field"
                      />
                    </div>
                  </div>

                  <div className="mt-8">
                    <label className="field-label">Special Equipment</label>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {SPECIAL_EQUIPMENT_OPTIONS.map((code) => (
                        <label key={code} className="flex items-center gap-3 rounded-2xl border border-slate-700/70 bg-slate-900/80 px-4 py-3 text-sm font-medium text-slate-200">
                          <input
                            type="checkbox"
                            checked={contractState.specialEquipment.includes(code)}
                            onChange={() => toggleSpecialEquipment(code)}
                            className="h-4 w-4 rounded border-slate-300"
                          />
                          <span>{code}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="lg:col-span-3 flex flex-col gap-5">
              <div className="panel p-8 sticky top-28 stagger-item">
                <h3 className="text-xs font-semibold text-slate-300 mb-5">Vertrags Export</h3>

                <div className="flex flex-col space-y-3">
                  <button
                    onClick={handleContractExport}
                    className="w-full flex items-center justify-center gap-3 text-white transition-all font-semibold cta-button cta-button-large"
                  >
                    <FileDown size={16} />
                    <span>Word Vertrag (.docx)</span>
                  </button>
                </div>


              </div>
            </div>
          </div>
        ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-14 stagger">
          
          {/* LINKES FELD: Eingabe-Bereich */}
          <div className="lg:col-span-9 flex flex-col gap-5">
            <div className="panel p-8 stagger-item">
              <h2 className="section-title mb-6">
                <Briefcase className="mr-2" size={18} />Basis-Spezifikationen
              </h2>
              
              <div className="grid grid-cols-2 gap-10 items-start">
                
                {/* Linke Spalte */}
                <div className="min-w-0 space-y-8">
                  <div>
                    <label className="field-label">Produktionsdatum</label>
                    <input
                      type="date"
                      value={activeCarState.prodDate}
                      onChange={(e) =>
                        setActiveCarState(prev => ({ ...prev, prodDate: e.target.value }))
                      }
                      className="field"
                    />
                  </div>

                  <div>
                    <label className="field-label">Department</label>
                    <select
                      value={activeCarState.dept}
                      onChange={(e) =>
                        setActiveCarState(prev => ({ ...prev, dept: e.target.value }))
                      }
                      className="field"
                    >
                      {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
                    </select>
                  </div>

                  <div>
                    <label className="field-label">Ziel-Land</label>
                    <select
                      value={activeCarState.country}
                      onChange={(e) =>
                        setActiveCarState(prev => ({ ...prev, country: e.target.value }))
                      }
                      className="field"
                    >
                      {COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                </div>
                
                {/* Rechte Spalte */}
                <div className="min-w-0 space-y-8">
                  <div>
                    <label className="field-label">Art der Nummer</label>
                    <select
                      value={activeCarState.numType}
                      onChange={(e) =>
                        setActiveCarState(prev => ({ ...prev, numType: e.target.value }))
                      }
                      className="field"
                    >
                      {NUMBER_TYPES.map(n => <option key={n} value={n}>{n}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="field-label">Nummer (max. 10 Stellen)</label>
                    <div className="relative">
                      <Hash className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                      <input 
                        type="text" 
                        maxLength={10} 
                        value={activeCarState.numValue} 
                        onChange={(e) =>
                          setActiveCarState(prev => ({
                            ...prev,
                            numValue: e.target.value.toUpperCase()
                          }))
                        } 
                        placeholder="Ident-No."
                        className="field pl-11 font-mono" 
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Sektion 2: Bulk Input */}
            <div className="panel p-8 stagger-item">
              <h2 className="section-title mb-4">
                <Code size={16} className="mr-2" />Options-Codes Bulk Input
              </h2>

              <textarea 
                rows="5"
                value={activeCarState.bulkCodes}
                onChange={(e) =>
                  setActiveCarState(prev => ({ ...prev, bulkCodes: e.target.value }))
                }
                placeholder="Codes hier einfügen (z.B. 1AB 2TC 3B3)..."
                className="field-textarea field-textarea--dark font-mono text-base leading-relaxed"
              ></textarea>
            </div>

            {/* Sektion 2b: Priced Codes */}
            <div className="panel p-8 stagger-item">
              <h2 className="section-title mb-4">
                <Code size={16} className="mr-2" />Codes mit Preisen
              </h2>
              <textarea 
                rows="6"
                value={activeCarState.pricedCodes}
                onChange={(e) =>
                  setActiveCarState(prev => ({ ...prev, pricedCodes: e.target.value }))
                }
                placeholder="Format: CODE Name Price (eine pro Zeile)&#10;1AB Brakes 500&#10;1AC Floor Mats 200&#10;109 Security Package VR6 1000"
                className="field-textarea field-textarea--dark font-mono text-base leading-relaxed"
              ></textarea>
            </div>

            {/* Sektion 3: Additions Checklist */}
            <div className="panel p-8 stagger-item">
              <AdditionsChecklist 
                backendUrl={BACKEND_URLS[activeCar]}
                onAdditionsChange={handleAdditionsChange}
              />
            </div>

          </div>

          {/* RECHTES FELD: Export Center */}
          <div className="lg:col-span-3 flex flex-col gap-5">
            
            <div className="panel p-8 sticky top-28 stagger-item">
               <h3 className="text-xs font-semibold text-slate-700 mb-5">Export Configuration</h3>
               
               <div className="space-y-5 mb-6">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-2">Net Mode</label>
                    <select
                      value={activeCarState.priceTypeNet}
                      onChange={(e) =>
                        setActiveCarState(prev => ({ ...prev, priceTypeNet: e.target.value }))
                      }
                      className="field text-sm"
                    >
                      {PRICE_TYPES_NET.map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-2">Total Mode</label>
                    <select
                      value={activeCarState.priceTypeTotal}
                      onChange={(e) =>
                        setActiveCarState(prev => ({ ...prev, priceTypeTotal: e.target.value }))
                      }
                      className="field text-sm"
                    >
                      {PRICE_TYPES_TOTAL.map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                  </div>
               </div>

               <div className="flex flex-col space-y-3">
                  <button 
                    onClick={() => handleExport('pdf', activeCarState, activeCar)} 
                    className="w-full flex items-center justify-center gap-3 text-white transition-all font-semibold cta-button cta-button-large"
                  >
                    <Download size={16} />
                    <span>PDF Protokoll</span>
                  </button>

                  <button 
                    onClick={() => handleExport('xlsx', activeCarState, activeCar)} 
                    className="w-full flex items-center justify-center gap-3 text-white transition-all font-semibold cta-button cta-button-large"
                  >
                    <FileText size={16} />
                    <span>Excel Export</span>
                  </button>
               </div>


            </div>
          </div>

        </div>
        )}

        {/* Footer Area */}
        <footer className="mt-20 pt-10 pb-32 text-center">
        </footer>
      </div>
    </div>
  );
}