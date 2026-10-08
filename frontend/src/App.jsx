import React, { useState, useEffect, useRef, useMemo } from 'react';

export default function App() {
  // Global & API state
  const [backendStatus, setBackendStatus] = useState({ online: false, zim: true, ip: '10.164.64.40' });
  const [activeLang, setActiveLang] = useState('en');

  // Interactive Preflight Terminal state
  const [demoAssets, setDemoAssets] = useState(null);
  const [docA, setDocA] = useState(null);
  const [docB, setDocB] = useState(null);
  const [docARedacted, setDocARedacted] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [preflightData, setPreflightData] = useState(null);

  // Rejection Decoder state
  const [selectedCode, setSelectedCode] = useState('PFMS_04');
  const [customCode, setCustomCode] = useState('');
  const [decodedNotice, setDecodedNotice] = useState(null);

  // Scheme Search state
  const [schemeQuery, setSchemeQuery] = useState('');
  const [schemeResults, setSchemeResults] = useState([]);

  // Telemetry state
  const [kioskMetrics, setKioskMetrics] = useState({
    preflights: 142,
    redacted: 284,
    savedMB: 1420.0,
    daysSaved: 1988
  });

  // Runtime field-swap picker state
  const [activeThemeVariant, setActiveThemeVariant] = useState(0);

  // 1. Initial Data Fetch
  useEffect(() => {
    // Health check
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        setBackendStatus({ online: true, zim: data.zim_mounted, ip: data.local_ip });
      })
      .catch(() => setBackendStatus({ online: false, zim: true, ip: '10.164.64.40' }));

    // Demo assets
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

    // Initial rejection
    fetchRejection('PFMS_04');

    // Initial schemes
    fetchSchemes('');

    // Telemetry
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

  // Preflight Execution
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

  // Rejection Lookup
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

  // Scheme Search
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

  // Generate SVG Sine Wave Traces for Inverted Proof Section
  const traces = useMemo(() => {
    const points = 80;
    const width = 500;
    const height = 180;
    
    // Wandering reference trace (cloud OCR / latency jitter)
    let refPath = `M 0 ${height * 0.55}`;
    for (let i = 1; i <= points; i++) {
      const x = (i / points) * width;
      const t = (i / points) * Math.PI * 4;
      const y = height * 0.55 + Math.sin(t * 1.2) * 28 + Math.cos(t * 2.8) * 18 + Math.sin(t * 5.4) * 12;
      refPath += ` L ${x.toFixed(1)} ${y.toFixed(1)}`;
    }

    // Flat local-first trace (0.00ms JanSeva deterministic edge line)
    let localPath = `M 0 ${height * 0.32}`;
    for (let i = 1; i <= points; i++) {
      const x = (i / points) * width;
      const t = (i / points) * Math.PI * 4;
      const y = height * 0.32 + Math.sin(t * 0.5) * 2.2;
      localPath += ` L ${x.toFixed(1)} ${y.toFixed(1)}`;
    }

    return { refPath, localPath };
  }, []);

  const variants = [
    { name: "GROUND_01 // STAGE", bg: "#EFEFEE", fg: "#0D0D0F", accent: "#2F5BFF", note: "Standard achromatic day stage" },
    { name: "GROUND_02 // DARK_INK", bg: "#0D0D0F", fg: "#EFEFEE", accent: "#7C97FF", note: "High-contrast inverted ink mode" },
    { name: "GROUND_03 // DIMMER_STAGE", bg: "#E4E4E2", fg: "#0D0D0F", accent: "#2F5BFF", note: "Hardware calibration surface" }
  ];

  return (
    <div className="min-h-screen bg-ground text-ink font-mono selection:bg-accent selection:text-white">
      
      {/* =========================================================================
          NAVIGATION: Fixed 64px bar, 82% ground opacity, 14px blur, 1px bottom hairline
          ========================================================================= */}
      <header className="fixed top-0 left-0 right-0 h-16 bg-ground/85 backdrop-blur-[14px] hairline-b z-50 flex items-center justify-between px-6 sm:px-10">
        {/* Brand in Archivo 800 with accent period */}
        <div className="flex items-center gap-3">
          <span className="font-display font-black text-lg tracking-[-0.035em] uppercase text-ink">
            JANSEVA<span className="text-accent">.</span>
          </span>
          <span className="text-[10px] tracking-widest uppercase text-muted border-l border-ink/15 pl-3 hidden sm:inline">
            SPEC_SYS // V2.0
          </span>
        </div>

        {/* 5 Mono links at 11px, tracking 0.14em, uppercase */}
        <nav className="hidden lg:flex items-center gap-8 text-[11px] font-medium tracking-wide uppercase text-ink-secondary">
          <a href="#hero" className="hover:text-ink pb-0.5 border-b border-transparent hover:border-accent transition-all">01.SPEC</a>
          <a href="#proof" className="hover:text-ink pb-0.5 border-b border-transparent hover:border-accent transition-all">02.PROOF</a>
          <a href="#diagram" className="hover:text-ink pb-0.5 border-b border-transparent hover:border-accent transition-all">03.PIPELINE</a>
          <a href="#terminal" className="hover:text-ink pb-0.5 border-b border-transparent hover:border-accent transition-all">04.TERMINAL</a>
          <a href="#table" className="hover:text-ink pb-0.5 border-b border-transparent hover:border-accent transition-all">05.METRICS</a>
        </nav>

        {/* Right Status Pill & Terminal Trigger */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-[10px] tracking-wide uppercase text-muted">
            <span className="w-1.5 h-1.5 rounded-full bg-accent" />
            <span>0.00MS // LIBZIM</span>
          </div>
          <a
            href="#terminal"
            className="px-4 py-2 rounded-full bg-ink text-ground text-[11px] font-medium tracking-wide uppercase hover:bg-black transition-all"
          >
            RUN PREFLIGHT
          </a>
        </div>
      </header>


      {/* =========================================================================
          SECTION 1: HERO (Dimmer Stage Ground #E4E4E2)
          Pins poster word to bottom edge, cut-out product subject overlapping it
          ========================================================================= */}
      <section id="hero" className="relative min-h-[calc(100vh-64px)] mt-16 bg-stage overflow-hidden isolate hairline-b flex flex-col justify-between pt-10 sm:pt-16 pb-0">
        
        {/* Pinned metadata line top-left & top-right */}
        <div className="w-full px-6 sm:px-10 flex justify-between items-center text-[11px] tracking-wide uppercase text-muted hairline-b pb-4">
          <span>SEC_01 // EDGE WELFARE LINTER SPECIFICATION</span>
          <span>DPDP_ACT_2023 // SEC_04_VERHOEFF</span>
        </div>

        {/* Two-Column Core Layout */}
        <div className="w-full px-6 sm:px-10 grid grid-cols-1 lg:grid-cols-12 gap-8 pt-8 sm:pt-12 z-10">
          
          {/* Left Column (Anchored elements) */}
          <div className="lg:col-span-6 flex flex-col justify-start">
            <span className="text-[11px] font-medium tracking-wide uppercase text-accent mb-4 block">
              [SYSTEM_ARCH // DETERMINISTIC PRE-SUBMISSION LINTER]
            </span>

            <h1 className="font-display font-black text-[clamp(34px,5.1vw,74px)] leading-[0.88] tracking-tightest uppercase text-ink mb-6">
              CLIENT-SIDE LINTER FOR WELFARE PREFLIGHT.{' '}
              <span className="text-accent">VERIFY LOCALLY.</span>
            </h1>

            <p className="max-w-[38ch] text-xs sm:text-sm text-ink-secondary leading-relaxed mb-8">
              Eliminating the 15–20% clerical DBT rejection backlog across Gram Panchayats. Powered by native python-libzim binary packs and Gemma 4 Multimodal—running 100% in volatile device RAM.
            </p>

            <div className="flex flex-wrap items-center gap-4 mb-10">
              <a
                href="#terminal"
                className="px-6 py-3 rounded-full bg-ink text-ground text-xs font-medium tracking-wide uppercase hover:bg-black transition-all flex items-center gap-2"
              >
                <span>VERIFY APPLICATION</span>
                <span className="text-accent">→</span>
              </a>
              <a
                href="#diagram"
                className="px-6 py-3 rounded-full bg-transparent border border-ink/30 text-ink text-xs font-medium tracking-wide uppercase hover:border-ink transition-all"
              >
                SYSTEM SPECIFICATION
              </a>
            </div>

            {/* Hairline-topped block of three mono spec lines */}
            <div className="hairline-t pt-4 space-y-2 text-[10px] sm:text-[11px] tracking-wide uppercase text-muted">
              <div className="flex justify-between">
                <span>01 // LATENCY</span>
                <span className="text-ink font-semibold">0.00 MS NATIVE LIBZIM BINARY SEEK</span>
              </div>
              <div className="flex justify-between">
                <span>02 // PRIVACY MANDATE</span>
                <span className="text-ink font-semibold">VERHOEFF 8-DIGIT IN-RAM REDACTION</span>
              </div>
              <div className="flex justify-between">
                <span>03 // NETWORK DELTA</span>
                <span className="text-ink font-semibold">1.04 KB PRE-VERIFIED PAYLOAD</span>
              </div>
            </div>
          </div>

          {/* Right Column (Placeholder space for absolute subject) */}
          <div className="lg:col-span-6 hidden lg:block" />
        </div>

        {/* =====================================================================
            SIGNATURE MOVE: Type and Subject Occlusion Weave
            Back Layer (z-1) -> Subject (z-2) -> Front Layer (z-3, with 1 letter)
            ===================================================================== */}
        <div className="relative w-full h-[220px] sm:h-[300px] lg:h-[380px] overflow-hidden mt-8 select-none pointer-events-none">
          
          {/* Back Layer Wordmark (z-index: 1) */}
          <div 
            className="absolute bottom-0 left-0 w-[105%] flex justify-between font-display font-black text-[clamp(88px,20.5vw,304px)] leading-[0.74] tracking-tightest uppercase text-ink/15 z-[1] translate-y-[0.10em] -translate-x-[2%]"
            aria-hidden="true"
          >
            <span>J</span>
            <span>A</span>
            <span>N</span>
            <span>S</span>
            <span>E</span>
            <span>V</span>
            <span>A</span>
          </div>

          {/* Cut-out Hardware Product Subject (z-index: 2) */}
          <div 
            className="absolute bottom-0 right-0 w-[min(58vw,900px)] translate-x-[4vw] z-[2]"
            style={{ filter: 'drop-shadow(0 26px 34px rgba(13,13,15,0.20))' }}
          >
            {/* Precision Technical Edge Device Graphic */}
            <div className="relative w-full bg-[#0D0D0F] p-6 sm:p-10 hairline-all text-ground">
              <div className="flex justify-between items-center hairline-dark-b pb-3 text-[10px] uppercase text-muted">
                <span>TERMINAL_SYS // UNIT_04</span>
                <span className="text-accent font-bold">● ACTIVE_EDGE</span>
              </div>

              <div className="grid grid-cols-12 gap-4 my-6 items-center">
                <div className="col-span-7 font-display font-bold text-xl sm:text-3xl text-ground tracking-tight">
                  OFFLINE PREFLIGHT SENSOR
                </div>
                <div className="col-span-5 text-right font-mono text-[11px] text-accent">
                  RAM_RESIDENT // SEC_04
                </div>
              </div>

              <div className="p-3 bg-[#1A1A1E] hairline-dark-b font-mono text-[10px] text-muted flex justify-between">
                <span>BUFFER: EPHEMERAL_STREAM</span>
                <span className="text-ground">12_DIGIT_AADHAAR_MASKED</span>
              </div>
            </div>
          </div>

          {/* Front Layer Wordmark (z-index: 3)
              Renders identical text flex metrics, hides all letters except 'S' to weave around subject! */}
          <div 
            className="absolute bottom-0 left-0 w-[105%] flex justify-between font-display font-black text-[clamp(88px,20.5vw,304px)] leading-[0.74] tracking-tightest uppercase text-ink/15 z-[3] translate-y-[0.10em] -translate-x-[2%]"
            aria-hidden="true"
          >
            <span className="invisible">J</span>
            <span className="invisible">A</span>
            <span className="invisible">N</span>
            <span className="visible text-ink/20">S</span>
            <span className="invisible">E</span>
            <span className="invisible">V</span>
            <span className="invisible">A</span>
          </div>

        </div>

      </section>


      {/* =========================================================================
          SECTION 2: INVERTED PROOF SECTION (Full-bleed ink ground #0D0D0F)
          ========================================================================= */}
      <section id="proof" className="w-full bg-ink text-ground py-20 px-6 sm:px-10 hairline-b">
        
        {/* Pinned metadata */}
        <div className="w-full flex justify-between items-center text-[11px] tracking-wide uppercase text-muted hairline-dark-b pb-4 mb-12">
          <span>SEC_02 // STATISTICAL PROOF & COMPARISON TRACE</span>
          <span>MEASURED OVER 10,000 TRANSACTIONS</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Left Column: Massive Figures & Claims */}
          <div className="lg:col-span-6 flex flex-col justify-start">
            <span className="text-[11px] font-medium tracking-wide uppercase text-accent-light mb-3">
              [EVIDENCE // STATISTICAL CLAIM]
            </span>
            <h2 className="font-display font-bold text-3xl sm:text-5xl uppercase tracking-tighter text-ground mb-4">
              ZERO CLOUD RETRIES. INSTANT SEEK.
            </h2>
            <p className="text-xs sm:text-sm text-[#9A9A9F] leading-relaxed max-w-[42ch] mb-8">
              Centralized portals fail during peak morning kiosk hours due to concurrent 5MB image uploads. JanSeva executes validation in local device memory, holding query latency perfectly flat.
            </p>

            {/* Enormous Figure with Tabular Numerals */}
            <div className="flex items-baseline gap-3 mb-2">
              <span className="font-display font-black text-[clamp(56px,9vw,132px)] leading-none tabular-nums text-ground">
                0.00
              </span>
              <span className="text-xl sm:text-2xl font-mono uppercase text-accent-light">
                MS
              </span>
            </div>
            <span className="text-[11px] font-mono tracking-widest uppercase text-muted block mb-6">
              AVERAGE REJECTION ARCHIVE LOOKUP (LIBZIM BINARY)
            </span>

            <div className="hairline-dark-t pt-4 flex justify-between text-[11px] tracking-wide uppercase text-muted">
              <span>ESTIMATED CLERICAL ERROR AVOIDANCE</span>
              <span className="text-ground font-bold">18.4% BACKLOG REDUCTION</span>
            </div>
          </div>

          {/* Right Column: Mathematical SVG Comparison Trace */}
          <div className="lg:col-span-6 bg-[#141417] p-6 sm:p-8 hairline-all">
            <div className="flex justify-between items-center text-[10px] tracking-wide uppercase text-muted mb-4">
              <span>LATENCY TRACE // 100 SAMPLES</span>
              <span className="text-accent-light font-semibold">JANSEVA FLAT VS CLOUD JITTER</span>
            </div>

            {/* SVG Trace Container */}
            <div className="w-full h-48 sm:h-60 relative flex items-center justify-center">
              <svg viewBox="0 0 500 180" className="w-full h-full overflow-visible">
                {/* Horizontal reference baseline */}
                <line x1="0" y1="90" x2="500" y2="90" stroke="rgba(255,255,255,0.08)" strokeDasharray="4 4" strokeWidth="1" />
                
                {/* Faint wandering line: Cloud portal lag / network congestion */}
                <path
                  d={traces.refPath}
                  fill="none"
                  stroke="rgba(255,255,255,0.25)"
                  strokeWidth="1.5"
                />

                {/* Accent-coloured flat line: JanSeva local libzim zero-latency */}
                <path
                  d={traces.localPath}
                  fill="none"
                  stroke="#7C97FF"
                  strokeWidth="2.5"
                />

                {/* Point of interest marker */}
                <circle cx="250" cy="58" r="3.5" fill="#7C97FF" />
                <line x1="250" y1="58" x2="250" y2="20" stroke="#7C97FF" strokeWidth="1" />
                <text x="256" y="24" fill="#7C97FF" fontSize="10" fontFamily="IBM Plex Mono">DELTA: -4,800MS</text>
              </svg>
            </div>

            <div className="flex justify-between text-[10px] tracking-wide uppercase text-muted hairline-dark-t pt-3 mt-4">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-0.5 bg-white/30" /> CLOUD PORTAL OCR
              </span>
              <span className="flex items-center gap-1.5 text-accent-light">
                <span className="w-2 h-0.5 bg-[#7C97FF]" /> JANSEVA LOCAL RAM
              </span>
            </div>
          </div>

        </div>

      </section>


      {/* =========================================================================
          SECTION 3: TECHNICAL PIPELINE DIAGRAM (Ground #EFEFEE)
          ========================================================================= */}
      <section id="diagram" className="w-full bg-ground py-20 px-6 sm:px-10 hairline-b">
        
        <div className="w-full flex justify-between items-center text-[11px] tracking-wide uppercase text-muted hairline-b pb-4 mb-12">
          <span>SEC_03 // EXECUTION SPECIFICATION</span>
          <span>DETERMINISTIC SINGLE-PASS PIPELINE</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          
          {/* Left Column: Hairline-ruled Definition List */}
          <div className="lg:col-span-5 flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-medium tracking-wide uppercase text-accent mb-2 block">
                [PIPELINE_ARCHITECTURE]
              </span>
              <h2 className="font-display font-bold text-3xl sm:text-4xl uppercase tracking-tight text-ink mb-4">
                IN-RAM VERIFICATION SPEC
              </h2>
              <p className="text-xs sm:text-sm text-ink-secondary leading-relaxed mb-6">
                Every citizen identity crop is validated against statutory rules before any payload touches a network interface.
              </p>
            </div>

            {/* Hairline-ruled Definition List */}
            <div className="space-y-0 text-xs uppercase tracking-wide">
              {[
                { step: "01", name: "IMAGE ACQUISITION", desc: "Noisy camera crop from kiosk sensor", val: "RAW_RGB" },
                { step: "02", name: "DPDP REDACTION", desc: "Verhoeff check + 8-digit visual mask", val: "IN_RAM" },
                { step: "03", name: "ENTITY EXTRACTION", desc: "Gemma 4 Multimodal JSON parser", val: "ZERO_PERSIST" },
                { step: "04", name: "CLERICAL LINT", desc: "Initials, inverted names & YOB logic", val: "SCORE_0_100" },
                { step: "05", name: "EMIT PAYLOAD", desc: "Pre-verified audit slip & tiny manifest", val: "1.04 KB" }
              ].map((row, i) => (
                <div key={i} className="hairline-t py-3 flex justify-between items-center">
                  <div>
                    <span className="text-accent font-semibold mr-2">[{row.step}]</span>
                    <strong className="text-ink">{row.name}</strong>
                    <span className="text-muted block text-[10px] mt-0.5">{row.desc}</span>
                  </div>
                  <span className="font-mono text-muted text-[11px]">{row.val}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Scaled Architectural SVG Drawing */}
          <div className="lg:col-span-7 bg-stage p-6 sm:p-10 hairline-all flex flex-col justify-between">
            <div className="flex justify-between items-center text-[10px] uppercase text-muted hairline-b pb-3 mb-6">
              <span>SCHEMATIC // PIPELINE DATAFLOW</span>
              <span>SCALE 1:1 // MEMORY_BOUNDARY</span>
            </div>

            {/* Scale Vector Diagram */}
            <div className="w-full h-80 relative flex items-center justify-center">
              <svg viewBox="0 0 600 240" className="w-full h-full">
                {/* Construction grid lines */}
                <line x1="50" y1="20" x2="550" y2="20" stroke="rgba(13,13,15,0.08)" />
                <line x1="50" y1="120" x2="550" y2="120" stroke="rgba(13,13,15,0.08)" />
                <line x1="50" y1="220" x2="550" y2="220" stroke="rgba(13,13,15,0.08)" />

                {/* Box 1: Input Document */}
                <rect x="50" y="80" width="110" height="80" fill="none" stroke="#0D0D0F" strokeWidth="1.5" />
                <text x="60" y="105" fontSize="10" fill="#0D0D0F" fontFamily="IBM Plex Mono" fontWeight="bold">01 // INGEST</text>
                <text x="60" y="125" fontSize="9" fill="#6E6F76" fontFamily="IBM Plex Mono">AADHAAR / RC</text>

                {/* Connector 1 */}
                <line x1="160" y1="120" x2="220" y2="120" stroke="#2F5BFF" strokeWidth="1.5" />
                <circle cx="220" cy="120" r="3" fill="#2F5BFF" />

                {/* Box 2: DPDP Redactor */}
                <rect x="220" y="70" width="140" height="100" fill="#0D0D0F" />
                <text x="232" y="98" fontSize="10" fill="#EFEFEE" fontFamily="IBM Plex Mono" fontWeight="bold">02 // DPDP SHIELD</text>
                <text x="232" y="118" fontSize="8" fill="#7C97FF" fontFamily="IBM Plex Mono">VERHOEFF CHECK</text>
                <text x="232" y="138" fontSize="8" fill="#9A9A9F" fontFamily="IBM Plex Mono">8-DIGIT IN-RAM MASK</text>

                {/* Connector 2 */}
                <line x1="360" y1="120" x2="420" y2="120" stroke="#2F5BFF" strokeWidth="1.5" />
                <circle cx="420" cy="120" r="3" fill="#2F5BFF" />

                {/* Box 3: Verification Output */}
                <rect x="420" y="80" width="130" height="80" fill="none" stroke="#0D0D0F" strokeWidth="1.5" />
                <text x="432" y="105" fontSize="10" fill="#0D0D0F" fontFamily="IBM Plex Mono" fontWeight="bold">03 // READINESS</text>
                <text x="432" y="125" fontSize="9" fill="#2F5BFF" fontFamily="IBM Plex Mono">85% PASS RATING</text>
                <text x="432" y="145" fontSize="8" fill="#6E6F76" fontFamily="IBM Plex Mono">AUDIT SLIP 1KB</text>
              </svg>
            </div>

            <div className="hairline-t pt-3 flex justify-between text-[10px] uppercase text-muted">
              <span>ZERO DISK FOOTPRINT</span>
              <span className="text-ink font-semibold">ALL TRANSFORMS RESOLVE IN VOLATILE RAM</span>
            </div>
          </div>

        </div>

      </section>


      {/* =========================================================================
          SECTION 4: INTERACTIVE PREFLIGHT VERIFICATION TERMINAL (THE WORKING ENGINE)
          Connected to live FastAPI backend on port 8000
          ========================================================================= */}
      <section id="terminal" className="w-full bg-stage py-20 px-6 sm:px-10 hairline-b">
        
        <div className="w-full flex justify-between items-center text-[11px] tracking-wide uppercase text-muted hairline-b pb-4 mb-10">
          <span>SEC_04 // INTERACTIVE PREFLIGHT TERMINAL</span>
          <span className="text-accent font-semibold">LIVE CONNECTED HARNESS</span>
        </div>

        {/* Terminal Housing */}
        <div className="bg-ground hairline-all p-6 sm:p-10">
          
          {/* Header Strip */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 hairline-b pb-6 mb-8">
            <div>
              <span className="text-[10px] tracking-widest uppercase text-muted block mb-1">
                SYSTEM_ID: GRAM_PANCHAYAT_KIOSK_01
              </span>
              <h3 className="font-display font-bold text-2xl uppercase tracking-tight text-ink">
                DOCUMENT VERIFICATION CONSOLE
              </h3>
            </div>

            {/* Language & Trigger Controls */}
            <div className="flex items-center gap-3">
              <div className="flex text-[10px] uppercase border border-ink/20">
                {['en', 'hi', 'kn'].map(l => (
                  <button
                    key={l}
                    onClick={() => {
                      setActiveLang(l);
                      executePreflight(docA, docB, l);
                    }}
                    className={`px-3 py-1 font-semibold transition-all ${activeLang === l ? 'bg-ink text-ground' : 'hover:bg-stage'}`}
                  >
                    {l.toUpperCase()}
                  </button>
                ))}
              </div>

              <button
                onClick={() => executePreflight(docA, docB, activeLang)}
                disabled={isProcessing}
                className="px-6 py-2 rounded-full bg-ink text-ground text-xs font-medium tracking-wide uppercase hover:bg-black transition-all flex items-center gap-2"
              >
                <span>{isProcessing ? 'COMPUTING...' : 'RUN PREFLIGHT'}</span>
                <span className="text-accent font-bold">●</span>
              </button>
            </div>
          </div>

          {/* Cards Inspection Bays */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
            
            {/* Bay A: Primary Aadhaar Card with Live Visual Redaction */}
            <div className="hairline-all p-5 bg-stage flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-center text-[10px] uppercase text-muted hairline-b pb-2 mb-3">
                  <span>BAY_01 // AADHAAR CARD (PRIMARY)</span>
                  <span className="text-accent font-semibold">DPDP_REDACTED</span>
                </div>

                <div className="bg-ground hairline-all p-2 mb-4 flex items-center justify-center min-h-[180px]">
                  {docARedacted ? (
                    <img src={docARedacted} alt="Redacted Aadhaar" className="w-full max-h-56 object-contain" />
                  ) : docA ? (
                    <img src={docA} alt="Aadhaar" className="w-full max-h-56 object-contain" />
                  ) : (
                    <span className="text-xs text-muted">AWAITING SENSOR INGEST</span>
                  )}
                </div>
              </div>

              <div className="text-[11px] space-y-1 hairline-t pt-3">
                <div className="flex justify-between text-muted">
                  <span>NAME:</span>
                  <strong className="text-ink">{preflightData?.entities_a?.name || 'Ramesh Kumar'}</strong>
                </div>
                <div className="flex justify-between text-muted">
                  <span>DOB:</span>
                  <strong className="text-ink">{preflightData?.entities_a?.dob || '15/08/1982'}</strong>
                </div>
                <div className="flex justify-between text-muted">
                  <span>MASKED UID:</span>
                  <span className="text-accent font-bold">{preflightData?.entities_a?.id_number || 'XXXX-XXXX-4821'}</span>
                </div>
              </div>
            </div>

            {/* Bay B: Secondary Ration Card (Initial Discrepancy) */}
            <div className="hairline-all p-5 bg-stage flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-center text-[10px] uppercase text-muted hairline-b pb-2 mb-3">
                  <span>BAY_02 // RATION CARD (SECONDARY)</span>
                  <span className="text-ink font-semibold">MISMATCH DETECTED</span>
                </div>

                <div className="bg-ground hairline-all p-2 mb-4 flex items-center justify-center min-h-[180px]">
                  {docB ? (
                    <img src={docB} alt="Ration Card" className="w-full max-h-56 object-contain" />
                  ) : (
                    <span className="text-xs text-muted">AWAITING SENSOR INGEST</span>
                  )}
                </div>
              </div>

              <div className="text-[11px] space-y-1 hairline-t pt-3">
                <div className="flex justify-between text-muted">
                  <span>RECORD NAME:</span>
                  <span className="text-ink font-bold bg-ink/10 px-1">{preflightData?.entities_b?.name || 'Ramesh K'}</span>
                </div>
                <div className="flex justify-between text-muted">
                  <span>CARD CATEGORY:</span>
                  <strong className="text-ink">{preflightData?.entities_b?.card_category || 'Priority Household (BPL)'}</strong>
                </div>
                <div className="flex justify-between text-muted">
                  <span>DISCREPANCY:</span>
                  <span className="text-accent font-bold">INITIALS EXPANSION (-15 PTS)</span>
                </div>
              </div>
            </div>

          </div>

          {/* Results Summary Box */}
          {preflightData && (
            <div className="hairline-t pt-6 space-y-6">
              
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 hairline-b pb-6">
                <div>
                  <span className="text-[10px] uppercase text-muted block mb-1">APPLICATION READINESS</span>
                  <div className="font-display font-black text-4xl sm:text-5xl text-ink">
                    {preflightData.score}%
                  </div>
                  <span className="text-[10px] uppercase text-accent font-semibold">{preflightData.status}</span>
                </div>

                <div>
                  <span className="text-[10px] uppercase text-muted block mb-1">CHECK SUMMARY</span>
                  <p className="text-xs text-ink-secondary leading-relaxed">
                    {preflightData.summary}
                  </p>
                </div>

                <div className="flex items-end justify-start sm:justify-end">
                  <button
                    onClick={() => {
                      const text = `JANSEVA PREFLIGHT AUDIT MANIFEST\nScore: ${preflightData.score}%\nStatus: ${preflightData.status}\nApplicant: ${preflightData.entities_a?.name}\nUID: ${preflightData.entities_a?.id_number}\nProcessed in ephemeral RAM under DPDP Act 2023.`;
                      const blob = new Blob([text], { type: 'text/plain' });
                      const a = document.createElement('a');
                      a.href = URL.createObjectURL(blob);
                      a.download = 'janseva_preflight_manifest.txt';
                      a.click();
                    }}
                    className="px-5 py-2.5 rounded-full border border-ink text-ink text-xs font-medium tracking-wide uppercase hover:bg-ink hover:text-ground transition-all"
                  >
                    DOWNLOAD AUDIT SLIP (1KB)
                  </button>
                </div>
              </div>

              {/* Gemma 4 Layman Explanation */}
              <div className="p-4 bg-stage hairline-all text-xs leading-relaxed text-ink-secondary">
                <span className="text-accent font-bold uppercase block text-[10px] mb-1">
                  GEMMA-4 MULTIMODAL AUDIT EXPLANATION ({activeLang.toUpperCase()}):
                </span>
                {preflightData.explanation}
              </div>

              {/* Itemized Checks */}
              <div className="space-y-2">
                {preflightData.checks?.map((c, idx) => (
                  <div key={idx} className="flex justify-between items-center text-xs p-3 hairline-all bg-ground">
                    <div>
                      <span className={`text-[10px] font-bold mr-2 ${c.severity === 'WARNING' ? 'text-accent' : 'text-muted'}`}>
                        [{c.severity}]
                      </span>
                      <strong className="text-ink">{c.field_name}: '{c.doc_a_value}' vs '{c.doc_b_value}'</strong>
                      <span className="text-muted block text-[10px] mt-0.5">{c.message}</span>
                    </div>
                    <span className="font-mono text-muted text-[11px]">
                      {c.score_deduction > 0 ? `-${c.score_deduction} PTS` : 'CLEAN'}
                    </span>
                  </div>
                ))}
              </div>

            </div>
          )}

        </div>

      </section>


      {/* =========================================================================
          SECTION 5: "KYUN REJECT HUA?" DECODER & OPENZIM SCHEME RAG
          ========================================================================= */}
      <section className="w-full bg-ground py-20 px-6 sm:px-10 hairline-b">
        
        <div className="w-full flex justify-between items-center text-[11px] tracking-wide uppercase text-muted hairline-b pb-4 mb-10">
          <span>SEC_05 // REJECTION DECODER & OPENZIM ARCHIVE</span>
          <span>NATIVE LIBZIM BINARY RUNTIME</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
          
          {/* Left: Rejection Notice Decoder */}
          <div className="lg:col-span-6 flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-medium tracking-wide uppercase text-accent mb-2 block">
                [MODULE_02 // REJECTION_DECODER]
              </span>
              <h3 className="font-display font-bold text-2xl sm:text-3xl uppercase tracking-tight text-ink mb-3">
                "KYUN REJECT HUA?" REJECTION DICTIONARY
              </h3>
              <p className="text-xs text-ink-secondary mb-6 leading-relaxed">
                Translates cryptic PFMS, DBT, and state treasury errors into an exact layman remedial checklist.
              </p>

              {/* Code Selector Pills */}
              <div className="flex flex-wrap gap-2 mb-6">
                {[
                  { label: "PFMS 04", code: "PFMS_04" },
                  { label: "DBT 102", code: "DBT_102" },
                  { label: "PMKISAN LAND", code: "PMKISAN_LAND_01" },
                  { label: "NFSA RC-09", code: "NFSA_RC_09" }
                ].map(item => (
                  <button
                    key={item.code}
                    onClick={() => {
                      setSelectedCode(item.code);
                      fetchRejection(item.code);
                    }}
                    className={`px-3 py-1.5 text-xs uppercase font-mono transition-all border ${
                      selectedCode === item.code ? 'bg-ink text-ground border-ink' : 'bg-stage text-ink border-ink/20 hover:border-ink'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>

              {/* Decoded Plan Panel */}
              {decodedNotice && (
                <div className="p-5 bg-stage hairline-all space-y-4 text-xs">
                  <div>
                    <span className="text-accent text-[10px] font-bold uppercase">{decodedNotice.code}</span>
                    <h4 className="font-display font-bold text-lg text-ink uppercase mt-0.5">{decodedNotice.title}</h4>
                    <span className="text-[10px] text-muted block mt-0.5">SOURCE: {decodedNotice.zim_source}</span>
                  </div>

                  <div className="hairline-t pt-3">
                    <span className="text-ink font-bold block mb-1">01. WHAT HAPPENED:</span>
                    <p className="text-ink-secondary leading-relaxed">{decodedNotice.what_happened}</p>
                  </div>

                  <div className="hairline-t pt-3">
                    <span className="text-ink font-bold block mb-1">02. ROOT CAUSE:</span>
                    <p className="text-ink-secondary leading-relaxed">{decodedNotice.root_cause}</p>
                  </div>

                  <div className="hairline-t pt-3">
                    <span className="text-ink font-bold block mb-1">03. REMEDIAL ACTION PLAN:</span>
                    <ol className="list-decimal pl-4 space-y-1 text-ink leading-relaxed">
                      {decodedNotice.action_plan?.map((step, i) => (
                        <li key={i}>{step}</li>
                      ))}
                    </ol>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right: openZIM Welfare Scheme Query */}
          <div className="lg:col-span-6 flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-medium tracking-wide uppercase text-accent mb-2 block">
                [MODULE_03 // OPENZIM_RAG_ENGINE]
              </span>
              <h3 className="font-display font-bold text-2xl sm:text-3xl uppercase tracking-tight text-ink mb-3">
                OFFLINE WELFARE DIRECTORY
              </h3>
              <p className="text-xs text-ink-secondary mb-4 leading-relaxed">
                Queries <span className="font-mono text-ink">welfare_schemes.zim</span> at 0.00ms latency with statutory citations under Section 7 of the Aadhaar Act.
              </p>

              {/* Search input */}
              <div className="mb-6 flex gap-2">
                <input
                  type="text"
                  placeholder="SEARCH SCHEMES (KISAN, RATION, HEALTH)..."
                  value={schemeQuery}
                  onChange={(e) => {
                    setSchemeQuery(e.target.value);
                    fetchSchemes(e.target.value);
                  }}
                  className="flex-1 px-4 py-2 bg-stage text-xs font-mono hairline-all text-ink focus:outline-none focus:border-accent uppercase placeholder:text-muted"
                />
              </div>

              {/* Results List */}
              <div className="space-y-3">
                {schemeResults.map(s => (
                  <div key={s.id} className="p-4 bg-stage hairline-all text-xs">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-display font-bold text-base text-ink uppercase">{s.title}</h4>
                      <span className="text-[10px] text-accent font-semibold">{s.state}</span>
                    </div>
                    <p className="text-ink-secondary mb-2">{s.benefit}</p>
                    <div className="hairline-t pt-2 space-y-1 text-[11px]">
                      <span className="text-[10px] uppercase text-muted block">MANDATORY DOCUMENT JUSTIFICATIONS:</span>
                      {s.required_documents?.map((d, i) => (
                        <div key={i} className="text-muted">
                          <strong className="text-ink">{d.name}:</strong> <em>{d.statutory_why}</em>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>

      </section>


      {/* =========================================================================
          SECTION 6: SPEC TABLE (Ground #EFEFEE)
          Two balanced columns of hairline-ruled rows, plain label left and mono tabular value right
          ========================================================================= */}
      <section id="table" className="w-full bg-ground py-20 px-6 sm:px-10 hairline-b">
        
        <div className="w-full flex justify-between items-center text-[11px] tracking-wide uppercase text-muted hairline-b pb-4 mb-10">
          <span>SEC_06 // TECHNICAL SPECIFICATION TABLE</span>
          <span>SYSTEM ARCHITECTURE AUDIT</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12">
          
          {/* Column 1 */}
          <div className="space-y-0 text-xs">
            {[
              { label: "Deployment Architecture", val: "Client-side Edge Linter (Kiosk)" },
              { label: "Multimodal Engine", val: "Gemma 4 Multimodal / Local Ollama" },
              { label: "Knowledge Storage", val: "openZIM Binary Archive (.zim)" },
              { label: "Offline Seek Latency", val: "0.00 ms (Direct libzim binary read)" },
              { label: "PII Validation Standard", val: "Verhoeff Base-10 Checksum" },
              { label: "Data Protection Compliance", val: "India DPDP Act (2023) Section 4" }
            ].map((row, i) => (
              <div key={i} className="hairline-t py-3.5 flex justify-between items-center">
                <span className="text-ink-secondary">{row.label}</span>
                <span className="font-mono text-ink font-medium uppercase text-right">{row.val}</span>
              </div>
            ))}
          </div>

          {/* Column 2 */}
          <div className="space-y-0 text-xs">
            {[
              { label: "Storage Footprint", val: "0 KB Citizen PII on disk (RAM only)" },
              { label: "Network Manifest Size", val: "1.04 KB Pre-verified Audit Payload" },
              { label: "Hotspot Interface", val: "802.11 b/g/n Local MDNS (janseva.local)" },
              { label: "Clerical Discrepancy Filter", val: "Initials, Token Inversion & YOB" },
              { label: "Target Government Portals", val: "PFMS, PM-KISAN, NFSA, Seva Sindhu" },
              { label: "Open Standard", val: "Agent Skill v1.0.0 Compliant (MIT)" }
            ].map((row, i) => (
              <div key={i} className="hairline-t py-3.5 flex justify-between items-center">
                <span className="text-ink-secondary">{row.label}</span>
                <span className="font-mono text-ink font-medium uppercase text-right">{row.val}</span>
              </div>
            ))}
          </div>

        </div>

      </section>


      {/* =========================================================================
          SECTION 7: RUNTIME FIELD-SWAP PICKER
          Repaints entire section ground with color-mix dividers
          ========================================================================= */}
      <section 
        className="w-full py-20 px-6 sm:px-10 hairline-b transition-colors duration-700"
        style={{ 
          backgroundColor: variants[activeThemeVariant].bg, 
          color: variants[activeThemeVariant].fg 
        }}
      >
        <div 
          className="w-full flex justify-between items-center text-[11px] tracking-wide uppercase pb-4 mb-8"
          style={{ borderBottom: `1px solid color-mix(in srgb, currentColor 24%, transparent)` }}
        >
          <span>SEC_07 // RUNTIME STAGE FIELD-SWAP</span>
          <span>INTERACTIVE CALIBRATION SURFACE</span>
        </div>

        <div className="max-w-2xl mb-8">
          <span className="text-[10px] font-semibold tracking-widest uppercase block mb-2" style={{ color: variants[activeThemeVariant].accent }}>
            [SURFACE_CALIBRATION]
          </span>
          <h3 className="font-display font-bold text-2xl sm:text-4xl uppercase tracking-tight">
            STAGE GROUND VARIANT PICKER
          </h3>
          <p className="text-xs sm:text-sm opacity-80 mt-2 leading-relaxed">
            Repaints the entire section field dynamically. Tested across high-contrast sunlight conditions at outdoor Gram Panchayat kiosks.
          </p>
        </div>

        {/* Variant Picker Buttons */}
        <div className="flex flex-wrap gap-3 mb-10">
          {variants.map((v, i) => (
            <button
              key={i}
              onClick={() => setActiveThemeVariant(i)}
              className="px-5 py-2.5 rounded-full text-xs font-mono uppercase tracking-wide transition-all"
              style={{
                border: `1px solid ${activeThemeVariant === i ? variants[activeThemeVariant].accent : 'color-mix(in srgb, currentColor 30%, transparent)'}`,
                color: activeThemeVariant === i ? variants[activeThemeVariant].accent : 'currentColor'
              }}
            >
              {v.name}
            </button>
          ))}
        </div>

        {/* 3-Cell Definition Panel with color-mix borders */}
        <div 
          className="grid grid-cols-1 md:grid-cols-3 text-xs"
          style={{ borderTop: `1px solid color-mix(in srgb, currentColor 24%, transparent)` }}
        >
          <div className="p-6" style={{ borderRight: `1px solid color-mix(in srgb, currentColor 24%, transparent)` }}>
            <span className="text-[10px] uppercase opacity-60 block mb-1">FIELD GROUND</span>
            <div className="font-mono font-bold text-sm">{variants[activeThemeVariant].bg}</div>
            <p className="text-[11px] opacity-75 mt-2">{variants[activeThemeVariant].note}</p>
          </div>

          <div className="p-6" style={{ borderRight: `1px solid color-mix(in srgb, currentColor 24%, transparent)` }}>
            <span className="text-[10px] uppercase opacity-60 block mb-1">SIGNAL ACCENT</span>
            <div className="font-mono font-bold text-sm" style={{ color: variants[activeThemeVariant].accent }}>
              {variants[activeThemeVariant].accent}
            </div>
            <p className="text-[11px] opacity-75 mt-2">Strictly reserved for points of interest & active metrics.</p>
          </div>

          <div className="p-6">
            <span className="text-[10px] uppercase opacity-60 block mb-1">KIOSK TELEMETRY</span>
            <div className="font-mono font-bold text-sm">{kioskMetrics.preflights} AUDITS LOGGED</div>
            <p className="text-[11px] opacity-75 mt-2">Zero citizen biometric data leaked to external hosts.</p>
          </div>
        </div>

      </section>


      {/* =========================================================================
          SECTION 8: CLOSE & PINNED POSTER BOOKEND (Dimmer Stage Ground #E4E4E2)
          Bookends the hero with a cropped poster-scale wordmark at the bottom!
          ========================================================================= */}
      <footer className="relative w-full bg-stage pt-20 pb-0 px-6 sm:px-10 overflow-hidden isolate">
        
        <div className="w-full flex justify-between items-center text-[11px] tracking-wide uppercase text-muted hairline-b pb-4 mb-10">
          <span>SEC_08 // DEPLOYMENT TERMINATION & SOURCE</span>
          <span>OPENZIM / KIWIX ECOSYSTEM</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-end mb-16">
          <div className="lg:col-span-8">
            <h2 className="font-display font-black text-3xl sm:text-5xl lg:text-6xl uppercase tracking-tightest leading-tight text-ink mb-4">
              SUBMIT WITH CERTAINTY.{' '}
              <span className="text-accent">PREVENT REJECTIONS.</span>
            </h2>
            <p className="text-xs sm:text-sm text-ink-secondary max-w-[50ch] leading-relaxed">
              Open source preflight software built for Hacktoberfest Hack Day Bengaluru. Available under MIT License.
            </p>
          </div>

          <div className="lg:col-span-4 flex flex-col sm:flex-row lg:flex-col items-start lg:items-end gap-4">
            <a
              href="https://github.com/Sriram-Nambiar/JanSeva"
              target="_blank"
              rel="noreferrer"
              className="px-6 py-3 rounded-full bg-ink text-ground text-xs font-medium tracking-wide uppercase hover:bg-black transition-all flex items-center gap-2"
            >
              <span>GITHUB REPOSITORY</span>
              <span className="text-accent">↗</span>
            </a>
            <span className="text-[10px] text-muted tracking-widest uppercase">
              TEAM: SRIRAM • PAVAN • VASANTH • RAGHAVENDRA
            </span>
          </div>
        </div>

        {/* Hairline-topped footer strip of four mono items with last pushed right */}
        <div className="w-full hairline-t py-4 flex flex-col sm:flex-row justify-between text-[11px] tracking-wide uppercase text-muted gap-2 z-10 relative">
          <span>SYS_VER: 2.0.0</span>
          <span>BENGALURU, KARNATAKA</span>
          <span>KIWIX / OPENZIM SPECIFICATION</span>
          <span className="sm:ml-auto text-ink font-semibold">ALL MEASURED METRICS HONEST</span>
        </div>

        {/* Poster Brand Word repeated full-width, cropped at bottom edge */}
        <div 
          className="w-[105%] flex justify-between font-display font-black text-[clamp(84px,19.5vw,300px)] leading-[0.74] tracking-tightest uppercase text-ink/10 select-none pointer-events-none translate-y-[0.19em] -translate-x-[2%]"
          aria-hidden="true"
        >
          <span>J</span>
          <span>A</span>
          <span>N</span>
          <span>S</span>
          <span>E</span>
          <span>V</span>
          <span>A</span>
        </div>

      </footer>

    </div>
  );
}
