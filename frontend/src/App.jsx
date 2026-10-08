import React, { useState, useEffect } from 'react';

export default function App() {
  // Global & API state
  const [backendStatus, setBackendStatus] = useState({ online: true, zim: true, ip: '10.164.64.40' });
  const [activeLang, setActiveLang] = useState('en');

  // Interactive Preflight Terminal state
  const [demoAssets, setDemoAssets] = useState(null);
  const [docA, setDocA] = useState(null);
  const [docB, setDocB] = useState(null);
  const [docARedacted, setDocARedacted] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [preflightData, setPreflightData] = useState(null);
  const [showRawUnmasked, setShowRawUnmasked] = useState(false);

  // Rejection Decoder state
  const [selectedCode, setSelectedCode] = useState('PFMS_04');
  const [decodedNotice, setDecodedNotice] = useState(null);

  // Scheme Search state
  const [schemeQuery, setSchemeQuery] = useState('');
  const [schemeResults, setSchemeResults] = useState([]);

  // openZIM Scraper state
  const [scrapeUrl, setScrapeUrl] = useState('https://myscheme.gov.in');
  const [scrapeTitle, setScrapeTitle] = useState('JanSeva Welfare Directory');
  const [scrapeLanguage, setScrapeLanguage] = useState('eng');
  const [scrapeMaxPages, setScrapeMaxPages] = useState(15);
  const [isScraping, setIsScraping] = useState(false);
  const [scrapeStatusMsg, setScrapeStatusMsg] = useState(null);
  const [scrapedPacksList, setScrapedPacksList] = useState([]);
  const [inspectingPackData, setInspectingPackData] = useState(null);
  const [viewingZimPack, setViewingZimPack] = useState('welfare_curated.zim');

  // Telemetry state
  const [kioskMetrics, setKioskMetrics] = useState({
    preflights: 142,
    redacted: 284,
    savedMB: 1420.0,
    daysSaved: 1988
  });

  // Initial Data Fetch
  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setBackendStatus({ online: true, zim: data.zim_mounted, ip: data.local_ip }))
      .catch(() => {});

    fetch('/api/demo-assets')
      .then(res => res.json())
      .then(data => {
        setDemoAssets(data);
        if (data.aadhaar && data.ration) {
          setDocA(data.aadhaar);
          setDocB(data.ration);
          executePreflight(data.aadhaar, data.ration, 'en');
        }
      })
      .catch(() => {});

    fetchRejection('PFMS_04');
    fetchSchemes('');
    fetchScrapedPacks();

    fetch('/api/telemetry')
      .then(res => res.json())
      .then(data => {
        setKioskMetrics({
          preflights: data.total_preflights,
          redacted: data.masked_cards,
          savedMB: data.bandwidth_saved_mb,
          daysSaved: data.estimated_backlog_days_saved
        });
      })
      .catch(() => {});
  }, []);

  const fetchScrapedPacks = async () => {
    try {
      const res = await fetch('/api/scraped-packs');
      if (res.ok) {
        const data = await res.json();
        setScrapedPacksList(data.packs || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleTriggerScrape = async (isCurated = false) => {
    setIsScraping(true);
    setScrapeStatusMsg(isCurated ? 'COMPILING CURATED PACK (0MS)...' : `CRAWLING ${scrapeUrl}...`);
    try {
      const payload = {
        url: scrapeUrl,
        output_name: isCurated ? 'welfare_curated.zim' : 'welfare_scraped.zim',
        title: scrapeTitle,
        language: scrapeLanguage,
        max_pages: parseInt(scrapeMaxPages) || 15,
        curated_pack: isCurated,
      };
      const res = await fetch('/api/scrape-to-zim', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const data = await res.json();
        setScrapeStatusMsg(`SUCCESS: COMPILED ${data.filename} (${data.filesize_kb} KB, ${data.article_count} SCHEMES)`);
        await fetchScrapedPacks();
        setViewingZimPack(data.filename);
      } else {
        const err = await res.json();
        setScrapeStatusMsg(`ERROR: ${err.detail || 'Scraping failed'}`);
      }
    } catch (e) {
      setScrapeStatusMsg(`NETWORK ERROR: ${e.message}`);
    } finally {
      setIsScraping(false);
    }
  };

  const handleInspectPack = async (filename) => {
    try {
      const res = await fetch(`/api/inspect-zim/${encodeURIComponent(filename)}`);
      if (res.ok) {
        const data = await res.json();
        setInspectingPackData(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const executePreflight = async (imgA, imgB, language = activeLang) => {
    setIsProcessing(true);
    try {
      const formData = new FormData();
      if (imgA) formData.append('doc_a_base64', imgA);
      if (imgB) formData.append('doc_b_base64', imgB);
      formData.append('lang', language);

      const res = await fetch('/api/preflight', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const result = await res.json();
        setPreflightData(result);
        setDocARedacted(result.doc_a_redacted_data_uri);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsProcessing(false);
    }
  };

  const fetchRejection = async (code) => {
    try {
      const res = await fetch('/api/decode-rejection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: code })
      });
      if (res.ok) {
        const data = await res.json();
        setDecodedNotice(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchSchemes = async (q) => {
    try {
      const res = await fetch(`/api/schemes?q=${encodeURIComponent(q)}&state=All&category=All&is_farmer=true`);
      if (res.ok) {
        const data = await res.json();
        setSchemeResults(data.schemes || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen bg-white text-[#171e19] font-inter antialiased selection:bg-[#ffe17c] selection:text-[#171e19]">
      
      {/* =========================================================================
          1. NAVIGATION: Fixed h-20 with #ffffff/90% blur, Anton logo with yellow dot, Inter links
          ========================================================================= */}
      <header className="fixed top-0 left-0 right-0 h-20 bg-white/90 backdrop-blur-md border-b border-[#171e19]/10 z-50 flex items-center justify-between px-6 sm:px-12">
        {/* Left: Brand Logo in Anton (uppercase, tall, condensed) with golden yellow dot */}
        <div className="flex items-center gap-1">
          <a href="#hero" className="font-anton font-normal text-3xl uppercase tracking-wider text-[#171e19] flex items-center">
            JANSEVA<span className="text-[#ffe17c] text-4xl leading-none">.</span>
          </a>
        </div>

        {/* Center: Clean Inter navigation links (weights 500-600) */}
        <nav className="hidden md:flex items-center gap-8 text-sm font-inter font-medium text-[#171e19]/70">
          <a href="#preflight" className="hover:text-[#171e19] transition-colors">Preflight Console</a>
          <a href="#contrast" className="hover:text-[#171e19] transition-colors">Why Edge</a>
          <a href="#features" className="hover:text-[#171e19] transition-colors">Features</a>
          <a href="#how-it-works" className="hover:text-[#171e19] transition-colors">How It Works</a>
          <a href="#openzim" className="hover:text-[#171e19] transition-colors">openZIM Pipeline</a>
          <a href="#decoder" className="hover:text-[#171e19] transition-colors">Decoder</a>
        </nav>

        {/* Right: Live offline badge in Inter and pill button in Inter (weights 600-700) */}
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 text-xs font-inter font-semibold text-[#171e19]/70">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>0MS OFFLINE</span>
          </div>

          <a
            href="#preflight"
            className="px-6 py-2.5 rounded-full bg-[#171e19] text-white font-inter font-semibold text-xs uppercase tracking-wider hover:bg-black transition-all shadow-sm"
          >
            RUN AUDIT
          </a>
        </div>
      </header>


      {/* =========================================================================
          2. HERO SECTION: Centered layout on 40px grid pattern, massive Anton headline with yellow highlight
          ========================================================================= */}
      <section id="hero" className="relative pt-36 pb-20 px-6 sm:px-12 bg-grid overflow-hidden border-b border-[#171e19]/10">
        <div className="max-w-5xl mx-auto text-center flex flex-col items-center">
          
          {/* Badge with yellow dot indicator in Inter font */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#171e19]/5 border border-[#171e19]/10 text-xs font-inter font-semibold uppercase tracking-widest text-[#171e19]/75 mb-8">
            <span className="w-2 h-2 rounded-full bg-[#ffe17c]"></span>
            <span>ACCEPTING EARLY ACCESS · DPDP ACT 2023 COMPLIANT</span>
          </div>

          {/* Headline in massive Anton font (uppercase, tall, condensed, 400 weight, tight leading) with yellow highlight */}
          <h1 className="font-anton font-normal text-[clamp(52px,9.5vw,140px)] tracking-tight leading-[0.88] uppercase text-[#171e19] mb-6">
            VERIFY WITHOUT<br />
            <span className="relative inline-block px-3">
              <span className="relative z-10">REJECTION</span>
              <span className="absolute inset-x-0 bottom-1 sm:bottom-3 top-3 sm:top-5 bg-[#ffe17c] -z-0"></span>
            </span>
          </h1>

          {/* Subheadline in clean Inter font (weight 400) */}
          <p className="font-inter font-normal text-base sm:text-xl text-[#171e19]/70 max-w-xl mx-auto leading-relaxed mb-10">
            Stop wrestling with documentation typos, server 503 crashes, and unmasked citizen PII. JanSeva is the single operating system for high-velocity welfare delivery.
          </p>

          {/* Side-by-side Waitlist/Quick Ingest Form (Inter input & Inter bold button) */}
          <div className="w-full max-w-md flex flex-col sm:flex-row items-center gap-3 mb-16">
            <input
              type="text"
              readOnly
              value="Citizen: Ramesh Kumar · Karnataka BPL"
              className="w-full px-5 py-3.5 bg-white border border-[#171e19]/20 rounded-lg text-xs sm:text-sm font-inter font-medium text-[#171e19] shadow-sm focus:outline-none"
            />
            <button
              onClick={() => {
                if (demoAssets) {
                  executePreflight(demoAssets.aadhaar, demoAssets.ration, activeLang);
                }
              }}
              className="w-full sm:w-auto px-8 py-3.5 bg-[#ffe17c] hover:bg-[#ffd859] text-[#171e19] font-inter font-bold text-sm tracking-wider uppercase rounded-lg transition-all shadow-sm active:scale-95 whitespace-nowrap"
            >
              GET ACCESS
            </button>
          </div>

          {/* =========================================================================
              ABSTRACT UI MOCKUP BROWSER FRAME
              ========================================================================= */}
          <div className="w-full max-w-6xl mx-auto border border-[#171e19]/10 rounded-2xl shadow-2xl bg-white overflow-hidden text-left">
            {/* Browser Window Header with Traffic Light Buttons */}
            <div className="h-11 bg-[#f8f9fa] border-b border-[#171e19]/10 px-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-[#ff5f56]"></span>
                <span className="w-3 h-3 rounded-full bg-[#ffbd2e]"></span>
                <span className="w-3 h-3 rounded-full bg-[#27c93f]"></span>
              </div>
              <div className="font-inter text-xs font-semibold text-[#171e19]/50 tracking-wider uppercase">
                JanSeva OS — Preflight Console & Edge Verifier
              </div>
              <div className="w-12"></div>
            </div>

            {/* Mockup Body: Interactive Preflight Verification Console */}
            <div id="preflight" className="p-6 sm:p-10 bg-white">
              
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 mb-8 border-b border-[#171e19]/10">
                <div>
                  <div className="font-inter text-xs font-semibold text-[#171e19]/50 tracking-widest uppercase mb-1">
                    SYSTEM_ID: GRAM_PANCHAYAT_KIOSK_01 · LIVE HARNESS
                  </div>
                  <h3 className="font-anton font-normal text-2xl sm:text-3xl uppercase tracking-tight text-[#171e19]">
                    DOCUMENT VERIFICATION CONSOLE
                  </h3>
                </div>

                <div className="flex items-center gap-3">
                  {/* Language Selector in Inter */}
                  <div className="flex border border-[#171e19]/20 rounded-lg overflow-hidden text-xs font-inter font-semibold uppercase">
                    {['en', 'hi', 'kn'].map(l => (
                      <button
                        key={l}
                        onClick={() => {
                          setActiveLang(l);
                          executePreflight(docA, docB, l);
                        }}
                        className={`px-3 py-1.5 transition-all ${activeLang === l ? 'bg-[#171e19] text-white font-bold' : 'bg-white hover:bg-slate-100 text-[#171e19]'}`}
                      >
                        {l}
                      </button>
                    ))}
                  </div>

                  <button
                    onClick={() => executePreflight(docA, docB, activeLang)}
                    disabled={isProcessing}
                    className="px-6 py-2 bg-[#ffe17c] hover:bg-[#ffd859] text-[#171e19] font-inter font-bold text-xs uppercase tracking-wider rounded-lg transition-all active:scale-95 disabled:opacity-50"
                  >
                    {isProcessing ? 'COMPUTING...' : 'RUN PREFLIGHT'}
                  </button>
                </div>
              </div>

              {/* Ingestion Bays */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-8">
                
                {/* Document Bay A: Aadhaar Card */}
                <div className="lg:col-span-4 bg-[#f8f9fa] border border-[#171e19]/10 rounded-xl p-5 flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-center text-xs font-inter font-semibold uppercase text-[#171e19]/60 pb-3 mb-3 border-b border-[#171e19]/10">
                      <span>BAY_01 // AADHAAR CARD</span>
                      <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded">
                        DPDP_REDACTED
                      </span>
                    </div>

                    <div className="bg-white border border-[#171e19]/10 rounded-lg p-2 mb-4 flex items-center justify-center min-h-[170px]">
                      {showRawUnmasked && docA ? (
                        <img src={docA} alt="Raw Aadhaar" className="w-full max-h-48 object-contain" />
                      ) : docARedacted ? (
                        <img src={docARedacted} alt="Redacted Aadhaar" className="w-full max-h-48 object-contain" />
                      ) : (
                        <span className="text-xs font-inter text-[#171e19]/50">AWAITING SENSOR INGEST</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-xs font-inter pt-3 border-t border-[#171e19]/10">
                    <button
                      onClick={() => setShowRawUnmasked(!showRawUnmasked)}
                      className="text-[#171e19]/60 hover:text-[#171e19] underline font-medium"
                    >
                      {showRawUnmasked ? 'MASK AADHAAR (DPDP)' : 'PEEK RAW INPUT'}
                    </button>
                    <span className="font-bold text-emerald-600">IN-RAM PROTECTED</span>
                  </div>
                </div>

                {/* Document Bay B: Ration Card */}
                <div className="lg:col-span-4 bg-[#f8f9fa] border border-[#171e19]/10 rounded-xl p-5 flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-center text-xs font-inter font-semibold uppercase text-[#171e19]/60 pb-3 mb-3 border-b border-[#171e19]/10">
                      <span>BAY_02 // RATION CARD</span>
                      <span className="font-bold text-[#171e19]">INGEST_ACTIVE</span>
                    </div>

                    <div className="bg-white border border-[#171e19]/10 rounded-lg p-2 mb-4 flex items-center justify-center min-h-[170px]">
                      {docB ? (
                        <img src={docB} alt="Ration Card" className="w-full max-h-48 object-contain" />
                      ) : (
                        <span className="text-xs font-inter text-[#171e19]/50">AWAITING SENSOR INGEST</span>
                      )}
                    </div>
                  </div>

                  <div className="text-xs font-inter text-[#171e19]/60 pt-3 border-t border-[#171e19]/10 flex justify-between">
                    <span>AHARA PORTAL MATCH</span>
                    <span className="font-bold text-[#171e19]">KARNATAKA BPL</span>
                  </div>
                </div>

                {/* Readiness Gauge & Scores */}
                <div className="lg:col-span-4 bg-[#171e19] text-white rounded-xl p-6 flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-center text-xs font-inter font-semibold text-white/60 pb-3 mb-4 border-b border-white/10 uppercase">
                      <span>READINESS SCORE</span>
                      <span className="text-[#ffe17c] font-bold">GEMMA 4 HARNESS</span>
                    </div>

                    <div className="flex items-baseline gap-2 mb-2">
                      <span className="font-anton font-normal text-7xl text-[#ffe17c] leading-none">
                        {preflightData ? preflightData.score : '85'}
                      </span>
                      <span className="font-anton font-normal text-3xl text-white/40">/100</span>
                    </div>

                    <p className="font-inter font-normal text-xs text-white/80 leading-relaxed mb-4">
                      {preflightData
                        ? preflightData.summary
                        : 'Demographic cross-checks complete. Minor clerical phonetic divergence flagged.'}
                    </p>
                  </div>

                  <div className="space-y-2 pt-4 border-t border-white/10 text-xs font-inter font-medium">
                    <div className="flex justify-between">
                      <span className="text-white/60">CRITICAL FLAGS:</span>
                      <span className="text-red-400 font-bold">{preflightData ? preflightData.critical_count : 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/60">WARNINGS (RECONCILED):</span>
                      <span className="text-[#ffe17c] font-bold">{preflightData ? preflightData.warning_count : 1}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/60">PASSED STATUTORY CHECKS:</span>
                      <span className="text-emerald-400 font-bold">{preflightData ? preflightData.pass_count : 3}</span>
                    </div>
                  </div>
                </div>

              </div>

              {/* Discrepancy Checks & AI Layman Translation in Inter */}
              {preflightData && (
                <div className="bg-[#f8f9fa] border border-[#171e19]/10 rounded-xl p-6">
                  <div className="font-inter text-xs font-semibold uppercase text-[#171e19]/60 mb-3 tracking-widest">
                    STATUTORY VERIFICATION CHECKLIST:
                  </div>

                  <div className="space-y-2 mb-6">
                    {preflightData.checks.map((c, i) => (
                      <div
                        key={i}
                        className="bg-white border border-[#171e19]/10 rounded-lg p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                      >
                        <div className="flex items-center gap-3">
                          <span
                            className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs ${
                              c.severity === 'PASS'
                                ? 'bg-emerald-100 text-emerald-800'
                                : c.severity === 'WARNING'
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {c.severity === 'PASS' ? '✓' : c.severity === 'WARNING' ? '!' : '✕'}
                          </span>
                          <span className="font-inter font-semibold text-sm text-[#171e19]">{c.field}</span>
                          <span className="font-inter font-normal text-xs text-[#171e19]/70 hidden sm:inline">{c.detail}</span>
                        </div>
                        <span
                          className={`text-xs font-inter font-bold px-2 py-1 rounded ${
                            c.severity === 'PASS'
                              ? 'bg-emerald-50 text-emerald-700'
                              : 'bg-amber-50 text-amber-700'
                          }`}
                        >
                          {c.severity}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="bg-[#171e19] text-white p-5 rounded-lg font-inter text-sm leading-relaxed">
                    <span className="font-inter text-xs text-[#ffe17c] font-bold block mb-1 uppercase tracking-wider">
                      GEMMA 4 EMPATHETIC AUDIT EXPLANATION ({activeLang.toUpperCase()}):
                    </span>
                    {preflightData.explanation}
                  </div>
                </div>
              )}

            </div>
          </div>

        </div>
      </section>


      {/* =========================================================================
          3. SOCIAL PROOF / LOGO BAR (Monochrome partners from reference screenshot)
          ========================================================================= */}
      <section className="w-full bg-white border-b border-[#171e19]/10 py-8 px-6 sm:px-12">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-around gap-6 opacity-60">
          <span className="font-inter font-bold text-xs uppercase tracking-widest text-[#171e19]">UIDAI DPDP 2023</span>
          <span className="font-inter font-bold text-xs uppercase tracking-widest text-[#171e19]">GEMMA 4 MULTIMODAL</span>
          <span className="font-inter font-bold text-xs uppercase tracking-widest text-[#171e19]">OPENZIM STANDARD</span>
          <span className="font-inter font-bold text-xs uppercase tracking-widest text-[#171e19]">KIWIX DESKTOP</span>
          <span className="font-inter font-bold text-xs uppercase tracking-widest text-[#171e19]">MEITY DIRECT BENEFIT</span>
        </div>
      </section>


      {/* =========================================================================
          4. HIGH-CONTRAST PROBLEM-SOLUTION SECTION (Matching media_1791439010783.png screenshot!)
             Anton for headings: "THE OLD WAY" & "THE FLUX WAY" (THE JANSEVA WAY).
             Inter for all supporting text, icons, and descriptions!
          ========================================================================= */}
      <section id="contrast" className="w-full bg-[#171e19] text-white py-20 px-6 sm:px-12 border-b border-[#171e19]/10">
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-start">
          
          {/* Left Side: "THE OLD WAY" with Anton heading and Inter text */}
          <div className="pt-2">
            <div className="flex items-center gap-3 mb-8">
              <span className="w-1.5 h-9 bg-[#b7c6c2]/40 rounded-full inline-block"></span>
              <h2 className="font-anton font-normal text-4xl sm:text-5xl uppercase tracking-tight text-[#b7c6c2]/80 leading-none">
                THE OLD WAY
              </h2>
            </div>

            <div className="space-y-8 pl-1">
              {[
                { title: "Scattered Cloud Uploads", desc: "Raw citizen Aadhaar numbers and passbooks uploaded to commercial third-party cloud APIs, violating India's DPDP Act 2023." },
                { title: "Peak-Hour Server 503 Crashes", desc: "Government portals crash during 10:00 AM rush because millions of rural kiosks upload heavy 5MB image scans simultaneously." },
                { title: "Weeks-Long Clerical Delays", desc: "15–20% of applications rejected weeks later due to simple spelling discrepancies between records (e.g. Ramesh K vs Ramesh Kumar)." },
                { title: "Cryptic SMS Rejection Codes", desc: "Citizens receive notices like 'PFMS Code 04' with zero explanation of what bank branch form to request." },
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-4">
                  <span className="w-5 h-5 rounded-full border border-red-500/50 text-red-400 font-bold flex items-center justify-center shrink-0 text-xs mt-0.5">
                    ✕
                  </span>
                  <div>
                    <h3 className="font-inter font-semibold text-white text-base mb-1">{item.title}</h3>
                    <p className="font-inter font-normal text-sm text-[#b7c6c2]/70 leading-relaxed">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Side: "THE JANSEVA WAY" (Matching card container with yellow bar from screenshot!) */}
          <div className="bg-[#1c241f] border border-[#b7c6c2]/15 rounded-2xl p-8 sm:p-12 shadow-2xl">
            <div className="flex items-center gap-3 mb-8">
              <span className="w-1.5 h-9 bg-[#ffe17c] rounded-full inline-block"></span>
              <h2 className="font-anton font-normal text-4xl sm:text-5xl uppercase tracking-tight text-white leading-none">
                THE JANSEVA WAY
              </h2>
            </div>

            <div className="space-y-8">
              {[
                { title: "In-RAM DPDP Masking", desc: "Visual black redaction and payload sanitization in temporary RAM. Zero citizen biometric data ever leaves local device memory." },
                { title: "0ms Offline openZIM Sync", desc: "Official statutory guidelines stored in native .zim archives using libzim. Queryable with zero dependence on congested servers." },
                { title: "Preflight Clerical Linter", desc: "Calculates Application Readiness score upfront, expanding initials and reconciling DOBs to stop rejections before submission." },
                { title: "Actionable Remedial Plans", desc: "Automated 3-part layman instructions in English, Hindi, and Kannada with exact bank Annexure-1 form details." },
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-4">
                  <span className="w-5 h-5 rounded-full border border-[#ffe17c] text-[#ffe17c] font-bold flex items-center justify-center shrink-0 text-xs mt-0.5">
                    ✓
                  </span>
                  <div>
                    <h3 className="font-inter font-semibold text-white text-base mb-1">{item.title}</h3>
                    <p className="font-inter font-normal text-sm text-white/80 leading-relaxed">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </section>


      {/* =========================================================================
          5. "BUILT FOR KIOSKS" SECTION (Matching "BUILT FOR FLOW" from reference screenshot!)
          ========================================================================= */}
      <section className="w-full bg-white py-20 px-6 sm:px-12 border-b border-[#171e19]/10">
        <div className="max-w-6xl mx-auto text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <h2 className="font-anton font-normal text-5xl sm:text-7xl uppercase tracking-tight text-[#171e19] leading-none">
              BUILT FOR{' '}
              <span className="relative inline-block px-2">
                <span className="relative z-10 text-[#ffe17c]">KIOSKS</span>
                <span className="absolute inset-x-0 bottom-2 top-4 bg-[#ffe17c]/25 -z-0"></span>
              </span>
            </h2>
          </div>
          <p className="font-inter font-normal text-base sm:text-lg text-[#171e19]/70 max-w-xl mx-auto">
            Engineered for edge hardware, rural touchscreens, and intermittent connectivity.
          </p>
        </div>
      </section>


      {/* =========================================================================
          6. BENTO FEATURE GRID (Anton headings + Inter descriptions & labels)
          ========================================================================= */}
      <section id="features" className="w-full bg-[#f8f9fa] py-24 px-6 sm:px-12 border-b border-[#171e19]/10">
        <div className="max-w-6xl mx-auto">
          
          <div className="text-center max-w-xl mx-auto mb-16">
            <span className="font-inter font-semibold text-xs uppercase tracking-widest text-[#171e19]/60 block mb-2">
              EDGE CAPABILITY MATRIX
            </span>
            <h2 className="font-anton font-normal text-4xl sm:text-6xl uppercase tracking-tight text-[#171e19]">
              THE PREFLIGHT BENTO
            </h2>
            <p className="font-inter font-normal text-sm sm:text-base text-[#171e19]/70 mt-3">
              High-performance modules engineered for edge hardware kiosks and rural Gram Panchayats.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Bento Card 1: Span 2 cols - DPDP Redaction */}
            <div className="md:col-span-2 bg-white border border-[#171e19]/10 rounded-2xl p-8 sm:p-10 shadow-sm flex flex-col justify-between">
              <div>
                <span className="font-inter font-semibold text-xs uppercase tracking-widest text-emerald-600 block mb-2">
                  MODULE 01 · DPDP ACT 2023
                </span>
                <h3 className="font-anton font-normal text-3xl uppercase tracking-tight text-[#171e19] mb-3">
                  IN-RAM AADHAAR VISUAL &amp; TEXT MASKING
                </h3>
                <p className="font-inter font-normal text-sm text-[#171e19]/70 leading-relaxed mb-6">
                  Every ingested identity document is processed strictly in temporary device RAM. The first 8 digits of Aadhaar are redacted on-screen, and strings are transformed to `XXXX-XXXX-1234` before any LLM inference.
                </p>
              </div>

              <div className="bg-[#f8f9fa] border border-[#171e19]/10 rounded-xl p-4 font-inter text-xs flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                  <span className="text-[#171e19]/50 block text-[10px] font-medium">VERHOEFF CHECKSUM VALIDATOR:</span>
                  <span className="font-semibold text-[#171e19]">ACTIVE (REJECTS 0/1 INITIALS)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 bg-emerald-100 text-emerald-800 rounded font-semibold text-xs">100% IN-RAM</span>
                  <span className="px-3 py-1 bg-[#ffe17c] text-[#171e19] rounded font-semibold text-xs">DPDP SAFE</span>
                </div>
              </div>
            </div>

            {/* Bento Card 2: Span 1 col - 0ms openZIM */}
            <div className="bg-[#171e19] text-white rounded-2xl p-8 sm:p-10 shadow-sm flex flex-col justify-between">
              <div>
                <span className="font-inter font-semibold text-xs uppercase tracking-widest text-[#ffe17c] block mb-2">
                  MODULE 02 · LIBZIM 3.13
                </span>
                <h3 className="font-anton font-normal text-3xl uppercase tracking-tight text-white mb-3">
                  0.00 MS SEEK LATENCY
                </h3>
                <p className="font-inter font-normal text-sm text-white/70 leading-relaxed mb-6">
                  Compiled `.zim` archives contain full-text Xapian indexing, reading statutory welfare rules locally with zero API latency.
                </p>
              </div>

              <div className="pt-4 border-t border-white/10 font-inter text-xs flex justify-between items-center text-white/60">
                <span>KIWIX ARCHIVE</span>
                <span className="text-[#ffe17c] font-bold">MOUNTED</span>
              </div>
            </div>

            {/* Bento Card 3: Span 1 col - Kyun Reject Hua */}
            <div className="bg-white border border-[#171e19]/10 rounded-2xl p-8 sm:p-10 shadow-sm flex flex-col justify-between">
              <div>
                <span className="font-inter font-semibold text-xs uppercase tracking-widest text-[#171e19]/50 block mb-2">
                  MODULE 03 · REMEDIAL ENGINE
                </span>
                <h3 className="font-anton font-normal text-3xl uppercase tracking-tight text-[#171e19] mb-3">
                  KYUN REJECT HUA?
                </h3>
                <p className="font-inter font-normal text-sm text-[#171e19]/70 leading-relaxed mb-6">
                  Translates confusing SMS codes (PFMS 04, DBT 102) into plain layman steps with exact bank Annexure-1 form instructions.
                </p>
              </div>

              <a href="#decoder" className="font-inter font-bold text-sm text-[#171e19] hover:underline flex items-center gap-1 uppercase tracking-wider">
                TRY DECODER →
              </a>
            </div>

            {/* Bento Card 4: Span 2 cols - Live openZIM Scraper */}
            <div className="md:col-span-2 bg-[#272727] text-white rounded-2xl p-8 sm:p-10 shadow-sm flex flex-col justify-between">
              <div>
                <span className="font-inter font-semibold text-xs uppercase tracking-widest text-[#ffe17c] block mb-2">
                  MODULE 04 · SCRAPER &amp; COMPILER
                </span>
                <h3 className="font-anton font-normal text-3xl uppercase tracking-tight text-white mb-3">
                  LIVE WELFARE PORTAL SCRAPER TO KIWIX .ZIM
                </h3>
                <p className="font-inter font-normal text-sm text-white/70 leading-relaxed mb-6">
                  Crawl MyScheme, state portals, and DBT registries directly into standard openZIM archives. Browse offline in our embedded in-app reader or open in Kiwix Desktop.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <a
                  href="#openzim"
                  className="px-6 py-2.5 bg-[#ffe17c] hover:bg-[#ffd859] text-[#171e19] font-inter font-bold text-xs uppercase tracking-wider rounded-lg transition-all"
                >
                  OPEN PIPELINE
                </a>
                <span className="font-inter font-medium text-xs text-white/50">OPENZIM &amp; LIBZIM COMPLIANT</span>
              </div>
            </div>

          </div>

        </div>
      </section>


      {/* =========================================================================
          7. HOW IT WORKS: 1:2 Column layout with massive numerals in Anton, descriptions in Inter
          ========================================================================= */}
      <section id="how-it-works" className="w-full bg-white py-24 px-6 sm:px-12 border-b border-[#171e19]/10">
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12">
          
          {/* Left Column: Sticky Anton Title */}
          <div className="lg:col-span-4">
            <div className="lg:sticky lg:top-28">
              <span className="font-inter font-semibold text-xs uppercase tracking-widest text-[#171e19]/60 block mb-2">
                VERIFICATION PIPELINE
              </span>
              <h2 className="font-anton font-normal text-5xl sm:text-7xl uppercase tracking-tight text-[#171e19] leading-none mb-4">
                HOW IT<br />WORKS
              </h2>
              <p className="font-inter font-normal text-sm text-[#171e19]/70 leading-relaxed">
                A deterministic 3-stage pipeline executing 100% on the edge kiosk before any packet reaches government servers.
              </p>
            </div>
          </div>

          {/* Right Column: 3 Vertical Steps with massive numerals */}
          <div className="lg:col-span-8 space-y-12">
            {[
              {
                num: "01",
                title: "INGEST & IN-RAM MASKING",
                desc: "Operator photographs physical citizen documents (Aadhaar, Ration Card). The In-RAM Redactor detects the Aadhaar photo badge and draws black privacy rectangles across the first 8 digits while validating the Verhoeff checksum.",
              },
              {
                num: "02",
                title: "PREFLIGHT CROSS-CHECK",
                desc: "Gemma 4 Multimodal Harness extracts name variants, expands South Indian initials (Ramesh K -> Ramesh Kumar), normalizes Year-of-Birth, and matches against scheme eligibility rules.",
              },
              {
                num: "03",
                title: "0MS OPENZIM RETRIEVAL & SUBMISSION",
                desc: "JanSeva queries local .zim knowledge packs to check statutory document justifications (Section 7 Aadhaar Act, APBS Seeding). Only verified, clean applications are submitted.",
              },
            ].map((step, i) => (
              <div key={i} className="border border-[#171e19]/10 rounded-2xl p-8 bg-[#f8f9fa] relative overflow-hidden group hover:border-[#171e19] transition-all">
                <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 mb-3">
                  <h3 className="font-anton font-normal text-2xl sm:text-3xl uppercase tracking-tight text-[#171e19]">
                    {step.title}
                  </h3>
                  <span className="font-anton font-normal text-6xl sm:text-7xl text-[#ffe17c]/50 group-hover:text-[#ffe17c] transition-colors leading-none">
                    {step.num}
                  </span>
                </div>
                <p className="font-inter font-normal text-sm sm:text-base text-[#171e19]/75 leading-relaxed max-w-xl">
                  {step.desc}
                </p>
              </div>
            ))}
          </div>

        </div>
      </section>


      {/* =========================================================================
          8. OPENZIM WELFARE ARCHIVER & IN-APP OFFLINE BROWSER
             Headings in Anton, buttons/labels/body in Inter!
          ========================================================================= */}
      <section id="openzim" className="w-full bg-[#f8f9fa] py-24 px-6 sm:px-12 border-b border-[#171e19]/10">
        <div className="max-w-6xl mx-auto">
          
          <div className="text-center max-w-xl mx-auto mb-16">
            <span className="font-inter font-semibold text-xs uppercase tracking-widest text-[#171e19]/60 block mb-2">
              OPENZIM STANDARD PIPELINE
            </span>
            <h2 className="font-anton font-normal text-4xl sm:text-6xl uppercase tracking-tight text-[#171e19]">
              CRAWL. COMPILE. BROWSE OFFLINE.
            </h2>
            <p className="font-inter font-normal text-sm sm:text-base text-[#171e19]/70 mt-3">
              Convert live government welfare portals into self-contained .zim archives. Browse them directly inside JanSeva or open in Kiwix Desktop.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-10">
            
            {/* Scraper Controls */}
            <div className="lg:col-span-6 bg-white border border-[#171e19]/10 rounded-2xl p-8 shadow-sm">
              <span className="font-inter font-semibold text-xs uppercase text-[#171e19]/50 block mb-2">
                PORTAL SEED PRESETS:
              </span>
              <div className="flex flex-wrap gap-2 mb-6">
                {[
                  { label: "MYSCHEME.GOV.IN", url: "https://myscheme.gov.in", title: "MyScheme National Portal" },
                  { label: "PM-KISAN", url: "https://pmkisan.gov.in", title: "PM-KISAN Samman Nidhi" },
                  { label: "SEVA SINDHU", url: "https://sevasindhu.karnataka.gov.in", title: "Karnataka Seva Sindhu" },
                  { label: "DBT BHARAT", url: "https://dbtbharat.gov.in", title: "Central DBT Bharat Registry" },
                ].map(p => (
                  <button
                    key={p.label}
                    onClick={() => {
                      setScrapeUrl(p.url);
                      setScrapeTitle(p.title);
                    }}
                    className={`px-3 py-1.5 text-xs font-inter font-semibold uppercase tracking-wider rounded-md border transition-all ${
                      scrapeUrl === p.url
                        ? 'bg-[#171e19] text-white border-[#171e19]'
                        : 'bg-[#f8f9fa] border-[#171e19]/15 hover:border-[#171e19]'
                    }`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>

              <div className="space-y-4 mb-6">
                <div>
                  <label className="font-inter font-medium text-xs uppercase text-[#171e19]/60 block mb-1">
                    TARGET PORTAL URL:
                  </label>
                  <input
                    type="text"
                    value={scrapeUrl}
                    onChange={(e) => setScrapeUrl(e.target.value)}
                    className="w-full px-4 py-2.5 bg-[#f8f9fa] border border-[#171e19]/20 rounded-lg font-inter text-xs text-[#171e19] focus:outline-none focus:border-[#171e19]"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="font-inter font-medium text-xs uppercase text-[#171e19]/60 block mb-1">
                      INDEX LANGUAGE:
                    </label>
                    <select
                      value={scrapeLanguage}
                      onChange={(e) => setScrapeLanguage(e.target.value)}
                      className="w-full px-3 py-2 bg-[#f8f9fa] border border-[#171e19]/20 rounded-lg font-inter text-xs text-[#171e19]"
                    >
                      <option value="eng">ENG (English)</option>
                      <option value="hin">HIN (Hindi)</option>
                      <option value="kan">KAN (Kannada)</option>
                    </select>
                  </div>
                  <div>
                    <label className="font-inter font-medium text-xs uppercase text-[#171e19]/60 block mb-1">
                      MAX PAGES:
                    </label>
                    <select
                      value={scrapeMaxPages}
                      onChange={(e) => setScrapeMaxPages(e.target.value)}
                      className="w-full px-3 py-2 bg-[#f8f9fa] border border-[#171e19]/20 rounded-lg font-inter text-xs text-[#171e19]"
                    >
                      <option value="10">10 Pages</option>
                      <option value="15">15 Pages</option>
                      <option value="25">25 Pages</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={() => handleTriggerScrape(false)}
                  disabled={isScraping}
                  className="px-6 py-3 bg-[#ffe17c] hover:bg-[#ffd859] text-[#171e19] font-inter font-bold text-xs uppercase tracking-wider rounded-lg transition-all active:scale-95 disabled:opacity-50"
                >
                  {isScraping ? 'CRAWLING & COMPILING...' : 'CRAWL & BUILD .ZIM'}
                </button>
                <button
                  onClick={() => handleTriggerScrape(true)}
                  disabled={isScraping}
                  className="px-5 py-3 bg-[#f8f9fa] hover:bg-[#e9ecef] text-[#171e19] border border-[#171e19]/15 font-inter text-xs uppercase font-semibold rounded-lg transition-all"
                >
                  CURATED PACK (0MS)
                </button>
              </div>

              {scrapeStatusMsg && (
                <div className="mt-4 p-3 bg-[#171e19] text-white rounded-lg font-inter text-xs">
                  {scrapeStatusMsg}
                </div>
              )}
            </div>

            {/* Local Storage Archive List */}
            <div className="lg:col-span-6 bg-white border border-[#171e19]/10 rounded-2xl p-8 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-center pb-3 mb-4 border-b border-[#171e19]/10 font-inter text-xs font-semibold text-[#171e19]/60 uppercase">
                  <span>LOCAL COMPILED .ZIM ARCHIVES</span>
                  <span>COUNT: {scrapedPacksList.length}</span>
                </div>

                <div className="space-y-3 max-h-[290px] overflow-y-auto pr-1">
                  {scrapedPacksList.map(pack => (
                    <div
                      key={pack.filename}
                      className="p-4 bg-[#f8f9fa] border border-[#171e19]/10 rounded-xl flex items-center justify-between gap-3"
                    >
                      <div>
                        <div className="font-anton font-normal text-lg uppercase tracking-tight text-[#171e19]">
                          {pack.filename}
                        </div>
                        <div className="font-inter font-normal text-xs text-[#171e19]/60">
                          {pack.title} · {pack.filesize_kb} KB
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setViewingZimPack(pack.filename)}
                          className="px-3 py-1.5 bg-[#ffe17c] hover:bg-[#ffd859] text-[#171e19] font-inter font-bold text-xs uppercase tracking-wider rounded transition-all"
                        >
                          BROWSE IN-APP ▶
                        </button>
                        <a
                          href={`/api/download-zim/${encodeURIComponent(pack.filename)}`}
                          download
                          className="px-3 py-1.5 bg-[#171e19] text-white font-inter font-semibold text-xs uppercase rounded hover:bg-black transition-all"
                        >
                          GET
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-[#171e19]/10 font-inter text-xs text-[#171e19]/60">
                100% openZIM / Kiwix Desktop compatible. Click BROWSE IN-APP to read offline directly inside JanSeva.
              </div>
            </div>

          </div>

          {/* Embedded In-App Offline Browser Frame */}
          {viewingZimPack && (
            <div className="w-full border border-[#171e19]/10 rounded-2xl shadow-2xl bg-white overflow-hidden mt-8">
              <div className="h-12 bg-[#171e19] text-white px-6 flex items-center justify-between text-xs font-inter font-medium">
                <div className="flex items-center gap-3">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#ffe17c] animate-pulse"></span>
                  <span className="font-bold tracking-wider uppercase">
                    IN-APP OFFLINE ZIM BROWSER // {viewingZimPack}
                  </span>
                  <span className="text-[10px] bg-white/10 px-2 py-0.5 rounded text-[#ffe17c] font-semibold">
                    0MS LOCAL STREAM VIA LIBZIM
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <a
                    href={`/api/zim-view/${encodeURIComponent(viewingZimPack)}/index.html`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-white/80 hover:text-white uppercase font-bold text-xs"
                  >
                    POPOUT FULLSCREEN ↗
                  </a>
                  <button
                    onClick={() => setViewingZimPack(null)}
                    className="px-2 py-0.5 bg-red-600/80 hover:bg-red-600 text-white rounded font-bold text-xs"
                  >
                    CLOSE [✕]
                  </button>
                </div>
              </div>

              <div className="w-full h-[640px] bg-white">
                <iframe
                  src={`/api/zim-view/${encodeURIComponent(viewingZimPack)}/index.html`}
                  title={`Offline ZIM Viewer - ${viewingZimPack}`}
                  className="w-full h-full border-none"
                />
              </div>
            </div>
          )}

        </div>
      </section>


      {/* =========================================================================
          9. "KYUN REJECT HUA?" ADMINISTRATIVE REJECTION DECODER
          ========================================================================= */}
      <section id="decoder" className="w-full bg-white py-24 px-6 sm:px-12 border-b border-[#171e19]/10">
        <div className="max-w-6xl mx-auto">
          
          <div className="text-center max-w-xl mx-auto mb-16">
            <span className="font-inter font-semibold text-xs uppercase tracking-widest text-[#171e19]/60 block mb-2">
              REMEDIAL KNOWLEDGE PACKS
            </span>
            <h2 className="font-anton font-normal text-4xl sm:text-6xl uppercase tracking-tight text-[#171e19]">
              KYUN REJECT HUA?
            </h2>
            <p className="font-inter font-normal text-sm sm:text-base text-[#171e19]/70 mt-3">
              Decode cryptic administrative SMS rejection codes into instant 3-step action plans.
            </p>
          </div>

          <div className="flex flex-wrap justify-center gap-2 mb-10">
            {[
              { code: "PFMS_04", label: "PFMS CODE 04 (NPCI SEEDING)" },
              { code: "DBT_102", label: "DBT ERROR 102 (DORMANT KYC)" },
              { code: "PMKISAN_LAND_01", label: "PM-KISAN LAND MUTATION" },
              { code: "NFSA_RC_09", label: "NFSA RC-09 (E-KYC PENDING)" },
              { code: "AYUSHMAN_07", label: "AYUSHMAN SECC MISMATCH" },
            ].map(item => (
              <button
                key={item.code}
                onClick={() => {
                  setSelectedCode(item.code);
                  fetchRejection(item.code);
                }}
                className={`px-4 py-2 font-inter text-xs uppercase font-semibold rounded-lg border transition-all ${
                  selectedCode === item.code
                    ? 'bg-[#171e19] text-white border-[#171e19]'
                    : 'bg-[#f8f9fa] border-[#171e19]/15 hover:border-[#171e19]'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          {decodedNotice && (
            <div className="bg-[#f8f9fa] border border-[#171e19]/10 rounded-2xl p-8 sm:p-12 shadow-sm max-w-4xl mx-auto">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 mb-6 border-b border-[#171e19]/10">
                <div>
                  <span className="font-inter text-xs font-bold uppercase text-red-600 bg-red-50 px-2 py-0.5 rounded">
                    {decodedNotice.code}
                  </span>
                  <h3 className="font-anton font-normal text-2xl sm:text-3xl uppercase tracking-tight text-[#171e19] mt-2">
                    {decodedNotice.title}
                  </h3>
                </div>
                <div className="font-inter font-medium text-xs text-[#171e19]/60">
                  PORTAL: {decodedNotice.issuing_portal}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                <div>
                  <h4 className="font-anton font-normal text-lg uppercase tracking-tight text-[#171e19] mb-2">1. WHAT HAPPENED:</h4>
                  <p className="font-inter font-normal text-sm text-[#171e19]/75 leading-relaxed bg-white p-4 rounded-xl border border-[#171e19]/10">
                    {decodedNotice.what_happened}
                  </p>
                </div>
                <div>
                  <h4 className="font-anton font-normal text-lg uppercase tracking-tight text-[#171e19] mb-2">2. THE ROOT CAUSE:</h4>
                  <p className="font-inter font-normal text-sm text-[#171e19]/75 leading-relaxed bg-white p-4 rounded-xl border border-[#171e19]/10">
                    {decodedNotice.root_cause}
                  </p>
                </div>
              </div>

              <div>
                <h4 className="font-anton font-normal text-xl uppercase tracking-tight text-[#171e19] mb-3">
                  3. EXACT REMEDIAL ACTION PLAN:
                </h4>
                <div className="space-y-2">
                  {decodedNotice.action_plan.map((step, idx) => (
                    <div
                      key={idx}
                      className="bg-white border border-[#171e19]/10 rounded-xl p-4 flex items-start gap-3"
                    >
                      <span className="font-anton font-normal text-lg text-[#ffe17c] leading-none shrink-0 mt-0.5">
                        {idx + 1}.
                      </span>
                      <p className="font-inter font-normal text-sm text-[#171e19]/80 leading-relaxed">{step}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

        </div>
      </section>


      {/* =========================================================================
          10. FINAL HIGH-ENERGY CTA: Background #ffe17c with massive Anton text
          ========================================================================= */}
      <section className="w-full bg-[#ffe17c] py-28 px-6 sm:px-12 text-[#171e19] text-center border-b border-[#171e19]/10">
        <div className="max-w-4xl mx-auto flex flex-col items-center">
          
          <span className="font-inter font-semibold text-xs uppercase tracking-widest text-[#171e19]/70 mb-3 block">
            EDGE WELFARE DEPLOYMENT READY
          </span>

          <h2 className="font-anton font-normal text-5xl sm:text-7xl lg:text-8xl uppercase tracking-tight leading-[0.9] text-[#171e19] mb-6">
            ZERO REJECTIONS.<br />
            ABSOLUTE PRIVACY.
          </h2>

          <p className="font-inter font-normal text-base sm:text-xl text-[#171e19]/80 max-w-xl mx-auto mb-10 leading-relaxed">
            Deploy JanSeva at your village panchayat or kiosk. 100% on-device preflight verification without transmitting citizen biometric data.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4">
            <a
              href="#preflight"
              className="px-8 py-4 bg-[#171e19] hover:bg-black text-white font-inter font-bold text-sm tracking-wider uppercase rounded-full shadow-xl hover:scale-105 transition-all"
            >
              LAUNCH KIOSK AUDIT
            </a>
            <a
              href="https://github.com/Sriram-Nambiar/JanSeva"
              target="_blank"
              rel="noreferrer"
              className="px-8 py-4 bg-white/80 hover:bg-white text-[#171e19] font-inter font-bold text-sm tracking-wider uppercase rounded-full border border-[#171e19]/20 transition-all"
            >
              GITHUB REPOSITORY ↗
            </a>
          </div>

        </div>
      </section>


      {/* =========================================================================
          11. FOOTER: Charcoal #171e19 with clean Inter metadata
          ========================================================================= */}
      <footer className="w-full bg-[#171e19] text-white py-16 px-6 sm:px-12">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-8 pb-12 border-b border-white/10">
          <div>
            <div className="font-anton font-normal text-3xl uppercase tracking-wider text-white flex items-center mb-2">
              JANSEVA<span className="text-[#ffe17c] text-4xl leading-none">.</span>
            </div>
            <p className="font-inter font-normal text-xs text-white/60 max-w-sm leading-relaxed">
              The client-side linter for Indian citizen welfare schemes. Built for Hacktoberfest Hack Day Bengaluru.
            </p>
          </div>

          <div className="flex flex-wrap gap-6 font-inter font-semibold text-xs uppercase tracking-wider text-white/70">
            <a href="#preflight" className="hover:text-white">Preflight</a>
            <a href="#openzim" className="hover:text-white">openZIM</a>
            <a href="#decoder" className="hover:text-white">Decoder</a>
            <a href="https://github.com/Sriram-Nambiar/JanSeva" target="_blank" rel="noreferrer" className="text-[#ffe17c] hover:underline">
              GitHub ↗
            </a>
          </div>
        </div>

        <div className="max-w-6xl mx-auto pt-8 flex flex-col sm:flex-row justify-between items-center gap-4 font-inter font-normal text-xs text-white/40">
          <span>MIT LICENSE · TEAM: SRIRAM · PAVAN · VASANTH · RAGHAVENDRA</span>
          <span>BENGALURU, KARNATAKA · LIBZIM 3.13 INTEGRATION</span>
        </div>
      </footer>

    </div>
  );
}
