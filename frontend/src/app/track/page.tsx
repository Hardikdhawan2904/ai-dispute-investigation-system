"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Shield, Home, ArrowLeft, LayoutDashboard, FileText } from "lucide-react";

export default function TrackSearchPage() {
  const router = useRouter();
  const [caseId, setCaseId] = useState("");
  const [error, setError] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const id = caseId.trim().toUpperCase();
    if (!id) {
      setError("Please enter a case reference.");
      return;
    }
    const cleanId = id.startsWith("CASE-") ? id : `CASE-${id}`;
    router.push(`/track/${cleanId}`);
  };

  return (
    <div className="min-h-screen bg-[#0F172A] text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-[#0B1120] px-4 sm:px-6 py-3 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-100">SecureBank</div>
              <div className="text-[10px] text-slate-400">Dispute Tracking Portal</div>
            </div>
          </Link>

          <div className="flex items-center gap-3 text-xs">
            <Link
              href="/"
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            >
              <Home className="w-3.5 h-3.5" /> Home Hub
            </Link>
            <Link
              href="/submit-dispute"
              className="hidden sm:flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            >
              <FileText className="w-3.5 h-3.5" /> File Dispute
            </Link>
            <Link
              href="/internal-review"
              className="hidden sm:flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            >
              <LayoutDashboard className="w-3.5 h-3.5 text-blue-400" /> Bank Ops
            </Link>
          </div>
        </div>
      </header>

      {/* Main Card */}
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="text-2xl font-extrabold text-white tracking-tight">SecureBank</div>
            <div className="text-xs text-slate-400 uppercase tracking-widest mt-1">Dispute Resolution Centre</div>
          </div>

          {/* Card */}
          <div className="bg-[#1E293B] border border-slate-700 rounded-2xl p-6 sm:p-8 shadow-2xl">
            <h1 className="text-xl font-bold text-white mb-1">Track Your Dispute</h1>
            <p className="text-xs text-slate-400 mb-6">
              Enter your case reference number to check live investigation progress and status.
            </p>

            <form onSubmit={handleSearch} className="space-y-4">
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Case Reference ID
                </label>
                <input
                  type="text"
                  value={caseId}
                  onChange={(e) => {
                    setCaseId(e.target.value);
                    setError("");
                  }}
                  placeholder="e.g. CASE-1001"
                  className="w-full px-4 py-3 bg-[#0F172A] border border-slate-700 rounded-xl text-white font-mono text-sm placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                />
                {error && <p className="text-xs text-rose-400 mt-1.5">{error}</p>}
              </div>

              <button
                type="submit"
                className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm rounded-xl transition-colors shadow-lg shadow-blue-600/20"
              >
                Search Case Status →
              </button>
            </form>

            <div className="mt-6 pt-6 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
              <Link href="/" className="flex items-center gap-1 hover:text-white transition-colors">
                <ArrowLeft className="w-3.5 h-3.5" /> Back to Home
              </Link>
              <Link href="/submit-dispute" className="text-blue-400 hover:underline">
                File a new dispute
              </Link>
            </div>
          </div>

          <div className="text-center mt-6 text-xs text-slate-500">
            For urgent assistance, contact SecureBank Support at 1800-XXX-XXXX
          </div>
        </div>
      </div>
    </div>
  );
}
