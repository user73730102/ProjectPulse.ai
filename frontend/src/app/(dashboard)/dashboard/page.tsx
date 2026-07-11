"use client";
import { useEffect, useState } from "react";
import { listNCRs, listSubmittals, listDocuments, NCR, Submittal, Document } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import Link from "next/link";

function StatCard({ label, value, sub, color }: { label: string; value: number | string; sub?: string; color: string }) {
  return (
    <div className="glass rounded-xl p-5 fade-up">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">{label}</p>
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string | null }) {
  const cls = severity === "Critical" ? "badge-critical" : severity === "Major" ? "badge-major" : "badge-minor";
  return (
    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${cls}`}>
      {severity || "Minor"}
    </span>
  );
}

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: "bg-slate-400", pending_review: "bg-blue-400", approved: "bg-emerald-400",
    closed: "bg-slate-600", voided: "bg-red-400",
    pending: "bg-slate-400", under_review: "bg-amber-400", rejected: "bg-red-400",
  };
  return <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${colors[status] || "bg-slate-400"}`} />;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [ncrs, setNCRs] = useState<NCR[]>([]);
  const [submittals, setSubmittals] = useState<Submittal[]>([]);
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([listNCRs(), listSubmittals(), listDocuments()])
      .then(([n, s, d]) => { setNCRs(n); setSubmittals(s); setDocs(d); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const criticalNCRs = ncrs.filter(n => n.severity === "Critical" && n.status !== "approved" && n.status !== "voided");
  const openNCRs = ncrs.filter(n => n.status === "draft" || n.status === "pending_review");
  const pendingSubmittals = submittals.filter(s => s.status === "pending" || s.status === "under_review");

  if (loading) {
    return (
      <div className="p-8">
        <div className="shimmer h-8 w-64 rounded-lg mb-8" />
        <div className="grid grid-cols-4 gap-4 mb-8">
          {[...Array(4)].map((_, i) => <div key={i} className="shimmer h-28 rounded-xl" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8 fade-up">
        <h1 className="text-2xl font-bold text-foreground">
          Good {new Date().getHours() < 12 ? "morning" : new Date().getHours() < 17 ? "afternoon" : "evening"},{" "}
          <span className="gradient-text">{user?.full_name?.split(" ")[0] || "there"}</span>
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Here&apos;s your project intelligence summary for DC-PROJ-2024-001
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Open NCRs" value={openNCRs.length} sub={`${criticalNCRs.length} critical`} color="text-amber-400" />
        <StatCard label="Pending Submittals" value={pendingSubmittals.length} sub="awaiting review" color="text-blue-400" />
        <StatCard label="Documents" value={docs.length} sub={`${docs.filter(d => d.is_processed).length} processed`} color="text-purple-400" />
        <StatCard label="Total NCRs" value={ncrs.length} sub={`${ncrs.filter(n => n.status === "approved").length} approved`} color="text-emerald-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent NCRs */}
        <div className="glass rounded-xl p-5 fade-up">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-foreground">Recent NCRs</h2>
            <Link href="/compliance" className="text-xs text-blue-400 hover:text-blue-300 transition-colors">View all →</Link>
          </div>
          <div className="space-y-2">
            {ncrs.slice(0, 5).map((ncr) => (
              <Link key={ncr.id} href={`/compliance/${ncr.id}`}
                className="flex items-start gap-3 p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors group">
                <StatusDot status={ncr.status} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <p className="text-xs font-mono text-muted-foreground">{ncr.ncr_number}</p>
                    <SeverityBadge severity={ncr.severity} />
                  </div>
                  <p className="text-xs text-foreground line-clamp-1">{ncr.deviation_description}</p>
                </div>
                <svg className="w-3.5 h-3.5 text-muted-foreground group-hover:text-foreground transition-colors shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            ))}
            {ncrs.length === 0 && (
              <p className="text-xs text-muted-foreground text-center py-4">No NCRs yet. Run a compliance check on a submittal to get started.</p>
            )}
          </div>
        </div>

        {/* Submittal Status */}
        <div className="glass rounded-xl p-5 fade-up">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-foreground">Submittals</h2>
            <Link href="/submittals" className="text-xs text-blue-400 hover:text-blue-300 transition-colors">View all →</Link>
          </div>
          <div className="space-y-2">
            {submittals.slice(0, 5).map((sub) => (
              <Link key={sub.id} href={`/submittals/${sub.id}`}
                className="flex items-center gap-3 p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors group">
                <StatusDot status={sub.status} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-foreground truncate">{sub.title}</p>
                  <p className="text-[10px] text-muted-foreground">{sub.vendor_name} · {sub.submittal_number}</p>
                </div>
                <span className="text-[10px] font-medium text-muted-foreground capitalize">
                  {sub.status.replace("_", " ")}
                </span>
              </Link>
            ))}
            {submittals.length === 0 && (
              <p className="text-xs text-muted-foreground text-center py-4">No submittals yet.</p>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-6 grid grid-cols-2 lg:grid-cols-3 gap-4 fade-up">
        <Link href="/rfi" className="glass rounded-xl p-5 hover:border-blue-500/30 transition-all group gradient-border">
          <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-3 group-hover:bg-blue-500/20 transition-colors">
            <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.7} d="M8.625 9.75a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375m-13.5 3.01c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.184-4.183a1.14 1.14 0 01.778-.332 48.294 48.294 0 005.83-.498c1.585-.233 2.708-1.626 2.708-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
            </svg>
          </div>
          <p className="text-sm font-semibold text-foreground">Ask RFI Assistant</p>
          <p className="text-xs text-muted-foreground mt-0.5">Query project documents with AI</p>
        </Link>

        <Link href="/documents" className="glass rounded-xl p-5 hover:border-purple-500/30 transition-all group">
          <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mb-3 group-hover:bg-purple-500/20 transition-colors">
            <svg className="w-4 h-4 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.7} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
          </div>
          <p className="text-sm font-semibold text-foreground">Upload Document</p>
          <p className="text-xs text-muted-foreground mt-0.5">Add specs, submittals, drawings</p>
        </Link>

        <Link href="/compliance" className="glass rounded-xl p-5 hover:border-amber-500/30 transition-all group">
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mb-3 group-hover:bg-amber-500/20 transition-colors">
            <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.7} d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
          </div>
          <p className="text-sm font-semibold text-foreground">Review NCRs</p>
          <p className="text-xs text-muted-foreground mt-0.5">{openNCRs.length} awaiting review</p>
        </Link>
      </div>
    </div>
  );
}
