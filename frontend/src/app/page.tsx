"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Shield,
  FileText,
  LayoutDashboard,
  Search,
  ArrowRight,
  CheckCircle2,
  Cpu,
  Lock,
  Activity,
  FileCheck,
  AlertTriangle,
  Scale,
  Bot,
  Mail,
  Zap,
  Users,
  ShieldCheck,
} from "lucide-react";

export default function Home() {
  const router = useRouter();
  const [searchCaseId, setSearchCaseId] = useState("");
  const [searchError, setSearchError] = useState("");
  const [apiStatus, setApiStatus] = useState<"checking" | "online" | "offline">("checking");

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    document.title = "BFSI Dispute Resolution Platform | Home Hub";

    // Ping backend status
    fetch(`${apiUrl}/health`, { method: "GET" })
      .then((res) => {
        if (res.ok) setApiStatus("online");
        else setApiStatus("offline");
      })
      .catch(() => {
        // Try fallback root endpoint
        fetch(`${apiUrl}/`, { method: "GET" })
          .then((res) => setApiStatus(res.ok ? "online" : "offline"))
          .catch(() => setApiStatus("offline"));
      });
  }, [apiUrl]);

  const handleTrackSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const id = searchCaseId.trim().toUpperCase();
    if (!id) {
      setSearchError("Please enter a valid Case Reference ID.");
      return;
    }
    const cleanId = id.startsWith("CASE-") ? id : `CASE-${id}`;
    router.push(`/track/${cleanId}`);
  };

  return (
    <div className="min-h-screen bg-[#0B1120] text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* ── Top Navigation Bar ────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-[#0B1120]/90 backdrop-blur-md border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-bold text-slate-100 text-base tracking-tight flex items-center gap-2">
                SecureBank <span className="text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 font-semibold border border-blue-500/20">AI Dispute Hub</span>
              </div>
              <p className="text-xs text-slate-400">Autonomous Banking Dispute & Fraud Resolution System</p>
            </div>
          </div>

          <div className="flex items-center gap-4 sm:gap-6">
            <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-300">
              <Link href="/submit-dispute" className="hover:text-blue-400 transition-colors flex items-center gap-1.5">
                <FileText className="w-4 h-4" /> Customer Portal
              </Link>
              <Link href="/track" className="hover:text-blue-400 transition-colors flex items-center gap-1.5">
                <Search className="w-4 h-4" /> Track Dispute
              </Link>
              <Link href="/internal-review" className="hover:text-blue-400 transition-colors flex items-center gap-1.5">
                <LayoutDashboard className="w-4 h-4 text-blue-400" /> Bank Ops Console
              </Link>
            </nav>

            {/* Backend API Health Badge */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-slate-900 border border-slate-800">
              <span className="relative flex h-2 w-2">
                <span
                  className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                    apiStatus === "online" ? "bg-emerald-400" : apiStatus === "offline" ? "bg-rose-400" : "bg-amber-400"
                  }`}
                />
                <span
                  className={`relative inline-flex rounded-full h-2 w-2 ${
                    apiStatus === "online" ? "bg-emerald-500" : apiStatus === "offline" ? "bg-rose-500" : "bg-amber-500"
                  }`}
                />
              </span>
              <span className="text-slate-300 capitalize">
                {apiStatus === "online" ? "API Live" : apiStatus === "offline" ? "API Offline" : "Checking API..."}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* ── Main Body ─────────────────────────────────────────────────── */}
      <main className="flex-1">
        {/* ── Hero Section ───────────────────────────────────────────── */}
        <section className="relative py-16 sm:py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center overflow-hidden">
          {/* Subtle Ambient Background Gradients */}
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-blue-600/10 blur-[120px] rounded-full pointer-events-none" />
          <div className="absolute top-1/3 left-1/3 w-[400px] h-[200px] bg-indigo-600/10 blur-[100px] rounded-full pointer-events-none" />

          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-blue-500/10 border border-blue-500/20 text-blue-400 mb-6">
            <Zap className="w-3.5 h-3.5 text-blue-400" /> Multi-Agent AI System Active
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-tight">
            Autonomous Banking Dispute & Fraud Resolution Platform
          </h1>

          <p className="mt-6 text-base sm:text-lg text-slate-300 max-w-3xl mx-auto leading-relaxed">
            Connecting customer dispute filing with multi-agent automated triage, real-time document evidence verification, fraud risk scoring, and internal bank operations review.
          </p>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/submit-dispute"
              className="px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm transition-all shadow-lg shadow-blue-600/30 flex items-center gap-2 group"
            >
              <FileText className="w-4 h-4" /> File a Customer Dispute
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>

            <Link
              href="/internal-review"
              className="px-6 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-100 font-semibold text-sm transition-all flex items-center gap-2"
            >
              <LayoutDashboard className="w-4 h-4 text-blue-400" /> Open Bank Ops Console
            </Link>
          </div>

          {/* Inline Track Quick Search */}
          <div className="mt-12 max-w-xl mx-auto bg-slate-900/90 border border-slate-800 p-2 sm:p-3 rounded-2xl shadow-xl">
            <form onSubmit={handleTrackSearch} className="flex flex-col sm:flex-row items-center gap-2">
              <div className="relative flex-1 w-full">
                <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={searchCaseId}
                  onChange={(e) => {
                    setSearchCaseId(e.target.value);
                    setSearchError("");
                  }}
                  placeholder="Enter Case Reference (e.g., CASE-1001)"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2.5 left-0 pl-10 pr-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>
              <button
                type="submit"
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-medium text-sm transition-colors whitespace-nowrap"
              >
                Track Case →
              </button>
            </form>
            {searchError && <p className="text-rose-400 text-xs mt-2 text-left px-2">{searchError}</p>}
          </div>
        </section>

        {/* ── Core Portal Cards Grid ─────────────────────────────────── */}
        <section className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Select Application Portal</h2>
            <p className="text-slate-400 text-sm mt-2">Access customer dispute submission or internal bank operations management</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Card 1: Customer Dispute Filing Portal */}
            <div className="bg-slate-900/80 border border-slate-800 hover:border-blue-500/50 rounded-2xl p-6 flex flex-col justify-between transition-all hover:shadow-xl hover:shadow-blue-500/5 group">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                    <FileText className="w-6 h-6 text-blue-400" />
                  </div>
                  <span className="text-[11px] font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    Customer Facing
                  </span>
                </div>

                <h3 className="text-xl font-bold text-white mb-2 group-hover:text-blue-400 transition-colors">
                  Customer Dispute Portal
                </h3>
                <p className="text-slate-400 text-sm leading-relaxed mb-6">
                  Guided 5-step dispute submission wizard for cardholders and account owners to report unauthorized or incorrect transactions.
                </p>

                <ul className="space-y-2.5 mb-8">
                  {[
                    "Live Account & Transaction Lookup",
                    "Automated Evidence Document Checklist",
                    "Dynamic Fraud Risk Questionnaire",
                    "Instant Submission Receipt & Case ID",
                  ].map((item, idx) => (
                    <li key={idx} className="flex items-center gap-2 text-xs text-slate-300">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <Link
                href="/submit-dispute"
                className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm text-center transition-colors flex items-center justify-center gap-2"
              >
                Launch Customer Portal <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {/* Card 2: Operations & Internal Review Console */}
            <div className="bg-slate-900/80 border border-slate-800 hover:border-indigo-500/50 rounded-2xl p-6 flex flex-col justify-between transition-all hover:shadow-xl hover:shadow-indigo-500/5 group">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                    <LayoutDashboard className="w-6 h-6 text-indigo-400" />
                  </div>
                  <span className="text-[11px] font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    Bank Ops & Compliance
                  </span>
                </div>

                <h3 className="text-xl font-bold text-white mb-2 group-hover:text-indigo-400 transition-colors">
                  Bank Operations Console
                </h3>
                <p className="text-slate-400 text-sm leading-relaxed mb-6">
                  Internal dashboard for fraud investigators, operations managers, and compliance officers to review and resolve dispute cases.
                </p>

                <ul className="space-y-2.5 mb-8">
                  {[
                    "Live Case Queue & Priority Triage",
                    "6 AI Subagents Analysis Breakdown",
                    "OCR Document Inspector & Risk Scores",
                    "Manual Override, Re-analysis & Dispatch",
                  ].map((item, idx) => (
                    <li key={idx} className="flex items-center gap-2 text-xs text-slate-300">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <Link
                href="/internal-review"
                className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm text-center transition-colors flex items-center justify-center gap-2"
              >
                Launch Bank Ops Console <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {/* Card 3: Dispute Tracking Portal */}
            <div className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-2xl p-6 flex flex-col justify-between transition-all hover:shadow-xl hover:shadow-slate-500/5 group md:col-span-2 lg:col-span-1">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center">
                    <Search className="w-6 h-6 text-slate-300" />
                  </div>
                  <span className="text-[11px] font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                    Self-Service
                  </span>
                </div>

                <h3 className="text-xl font-bold text-white mb-2 group-hover:text-slate-200 transition-colors">
                  Track Dispute Status
                </h3>
                <p className="text-slate-400 text-sm leading-relaxed mb-6">
                  Check live investigation progress, audit logs, requested evidence, and resolution status using your unique Case Reference ID.
                </p>

                <ul className="space-y-2.5 mb-8">
                  {[
                    "Real-time SLA Timeline & Case Stage",
                    "Additional Evidence Document Upload",
                    "Audit Trail & Communication Logs",
                    "Instant Status Updates & Outcome",
                  ].map((item, idx) => (
                    <li key={idx} className="flex items-center gap-2 text-xs text-slate-300">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <Link
                href="/track"
                className="w-full py-3 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-semibold text-sm text-center transition-colors flex items-center justify-center gap-2"
              >
                Track a Case <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </section>

        {/* ── Architecture & AI Agents Section ───────────────────────── */}
        <section className="py-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-slate-800/80 mt-8">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20 mb-3">
              <Cpu className="w-3.5 h-3.5" /> Intelligence Engine
            </div>
            <h2 className="text-2xl sm:text-4xl font-bold text-white tracking-tight">Multi-Agent AI Investigation Architecture</h2>
            <p className="text-slate-400 text-sm max-w-2xl mx-auto mt-2">
              Six specialized AI agents work synchronously to evaluate evidence, check banking compliance policies, detect fraud, and formulate resolution decisions.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {[
              {
                agent: "Agent 1",
                name: "Autonomous Triage Agent",
                icon: Bot,
                color: "text-blue-400",
                bg: "bg-blue-500/10",
                border: "border-blue-500/20",
                desc: "Ingests raw dispute payload, validates customer data against core banking database, and assigns initial risk priority.",
              },
              {
                agent: "Agent 2",
                name: "OCR Document Inspector",
                icon: FileCheck,
                color: "text-emerald-400",
                bg: "bg-emerald-500/10",
                border: "border-emerald-500/20",
                desc: "Executes Tesseract OCR on uploaded evidence, extracting merchant names, transaction dates, amounts, and verifying image integrity.",
              },
              {
                agent: "Agent 3",
                name: "Transaction Fraud Investigator",
                icon: AlertTriangle,
                color: "text-amber-400",
                bg: "bg-amber-500/10",
                border: "border-amber-500/20",
                desc: "Runs multi-factor fraud analysis (OTP exposure, remote access apps, phishing, device loss) and calculates fraud risk scores.",
              },
              {
                agent: "Agent 4",
                name: "Policy & Compliance Agent",
                icon: Scale,
                color: "text-purple-400",
                bg: "bg-purple-500/10",
                border: "border-purple-500/20",
                desc: "Evaluates dispute against RBI/BFSI regulatory frameworks, liability shift rules, zero-liability timelines, and required document checklists.",
              },
              {
                agent: "Agent 5",
                name: "Resolution Decision Engine",
                icon: ShieldCheck,
                color: "text-indigo-400",
                bg: "bg-indigo-500/10",
                border: "border-indigo-500/20",
                desc: "Synthesizes agent outputs to output a confidence-weighted decision recommendation (APPROVED, REJECTED, or MANUAL REVIEW).",
              },
              {
                agent: "Agent 6",
                name: "Customer Communication Agent",
                icon: Mail,
                color: "text-sky-400",
                bg: "bg-sky-500/10",
                border: "border-sky-500/20",
                desc: "Generates personalized, compliant notifications, formal dispute decision letters, and missing document requests.",
              },
            ].map((item, idx) => {
              const IconComp = item.icon;
              return (
                <div key={idx} className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`w-9 h-9 rounded-lg ${item.bg} border ${item.border} flex items-center justify-center`}>
                      <IconComp className={`w-4 h-4 ${item.color}`} />
                    </div>
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{item.agent}</span>
                      <h4 className="text-sm font-semibold text-slate-100">{item.name}</h4>
                    </div>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
                </div>
              );
            })}
          </div>
        </section>

        {/* ── Platform Metrics Bar ───────────────────────────────────── */}
        <section className="py-12 bg-slate-900/40 border-y border-slate-800">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
              <div>
                <div className="text-2xl sm:text-3xl font-extrabold text-blue-400 font-mono">&lt; 60s</div>
                <div className="text-xs text-slate-400 mt-1 font-medium">Automated Triage Time</div>
              </div>
              <div>
                <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400 font-mono">99.4%</div>
                <div className="text-xs text-slate-400 mt-1 font-medium">OCR Extraction Accuracy</div>
              </div>
              <div>
                <div className="text-2xl sm:text-3xl font-extrabold text-indigo-400 font-mono">6 AI Agents</div>
                <div className="text-xs text-slate-400 mt-1 font-medium">Synchronous Ecosystem</div>
              </div>
              <div>
                <div className="text-2xl sm:text-3xl font-extrabold text-purple-400 font-mono">100% Audit</div>
                <div className="text-xs text-slate-400 mt-1 font-medium">Immutable Case History</div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* ── Footer ────────────────────────────────────────────────────── */}
      <footer className="bg-[#0B1120] border-t border-slate-800 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-blue-400" />
            <span className="font-semibold text-slate-300">SecureBank BFSI Dispute Resolution Engine v1.0</span>
          </div>
          <div className="flex items-center gap-6">
            <Link href="/submit-dispute" className="hover:text-slate-300 transition-colors">Customer Portal</Link>
            <Link href="/track" className="hover:text-slate-300 transition-colors">Track Dispute</Link>
            <Link href="/internal-review" className="hover:text-slate-300 transition-colors">Bank Ops Console</Link>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400">
            <Lock className="w-3.5 h-3.5 text-emerald-400" /> 256-Bit Encrypted Banking Standard
          </div>
        </div>
      </footer>
    </div>
  );
}
