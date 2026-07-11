"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getNCR, approveNCR, voidNCR, NCR } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function NCRDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const [ncr, setNCR] = useState<NCR | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");

  const id = Number(params.id);

  useEffect(() => {
    if (!id) return;
    getNCR(id).then(setNCR).catch(e => setError(e.message)).finally(() => setLoading(false));
  }, [id]);

  const handleApprove = async () => {
    if (!confirm("Approve this NCR? It will become part of the official project record.")) return;
    setActionLoading(true);
    try {
      const updated = await approveNCR(id);
      setNCR(updated);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleVoid = async () => {
    if (!confirm("Void this NCR? It will be marked as voided.")) return;
    setActionLoading(true);
    try {
      const updated = await voidNCR(id);
      setNCR(updated);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <div className="p-8 max-w-5xl mx-auto"><div className="h-64 bg-card rounded-xl shimmer" /></div>;
  if (!ncr) return <div className="p-8 max-w-5xl mx-auto text-red-400">NCR not found or {error}</div>;

  const canApprove = (user?.role === "engineer" || user?.role === "pm") && (ncr.status === "draft" || ncr.status === "pending_review");
  const canVoid = user?.role === "pm" && ncr.status !== "closed" && ncr.status !== "voided";

  return (
    <div className="p-8 max-w-5xl mx-auto pb-24">
      {/* Header */}
      <div className="mb-6 fade-up flex items-start justify-between">
        <div>
          <Link href="/compliance" className="text-xs text-blue-400 hover:text-blue-300 mb-2 inline-block">← Back to NCRs</Link>
          <div className="flex items-center gap-3 mt-1">
            <h1 className="text-2xl font-bold text-foreground font-mono">{ncr.ncr_number}</h1>
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
              ncr.severity === "Critical" ? "badge-critical" : ncr.severity === "Major" ? "badge-major" : "badge-minor"
            }`}>{ncr.severity}</span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full border badge-draft uppercase">
              {ncr.status.replace("_", " ")}
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-2 max-w-2xl">{ncr.deviation_description}</p>
        </div>
        
        {/* Actions */}
        <div className="flex gap-2">
          {canApprove && (
            <button onClick={handleApprove} disabled={actionLoading}
              className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-medium transition-colors disabled:opacity-50 shadow-lg shadow-emerald-500/20">
              Approve NCR
            </button>
          )}
          {canVoid && (
            <button onClick={handleVoid} disabled={actionLoading}
              className="px-4 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/20 text-sm font-medium transition-colors disabled:opacity-50">
              Void
            </button>
          )}
        </div>
      </div>

      {error && <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">{error}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 fade-up">
        {/* Submittal Details */}
        <div className="glass rounded-xl p-6 gradient-border">
          <h2 className="text-sm font-semibold text-foreground border-b border-border pb-3 mb-4 flex items-center gap-2">
            <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z" />
            </svg>
            Submitted Value
          </h2>
          <div className="space-y-4">
            <div>
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-1">Source Submittal</p>
              <Link href={`/submittals/${ncr.submittal_id}`} className="text-sm font-medium text-blue-400 hover:underline">
                {ncr.submittal_number || `Submittal #${ncr.submittal_id}`}
              </Link>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-1">Vendor</p>
              <p className="text-sm text-foreground">{ncr.vendor_name || "Unknown"}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-2">What they submitted</p>
              <div className="bg-secondary/50 rounded-lg p-4 border border-border">
                <p className="text-sm text-red-400 font-mono whitespace-pre-wrap">{ncr.submitted_value}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Spec Clause */}
        <div className="glass rounded-xl p-6 gradient-border">
          <h2 className="text-sm font-semibold text-foreground border-b border-border pb-3 mb-4 flex items-center gap-2">
            <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
            </svg>
            Project Specification
          </h2>
          <div className="space-y-4">
            <div>
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-1">Spec Section Reference</p>
              <p className="text-sm font-medium text-foreground">
                Clause {ncr.clause_number} — {ncr.clause_title}
              </p>
              {ncr.clause_page && <p className="text-xs text-muted-foreground mt-0.5">Page {ncr.clause_page}</p>}
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-2">What is required</p>
              <div className="bg-secondary/50 rounded-lg p-4 border border-border">
                <p className="text-sm text-emerald-400 font-mono whitespace-pre-wrap">{ncr.required_value}</p>
              </div>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-2">Original Clause Text</p>
              <div className="bg-background rounded-lg p-4 border border-border overflow-y-auto max-h-48 text-xs text-muted-foreground whitespace-pre-wrap">
                {ncr.clause_content}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* AI Confidence Banner */}
      {ncr.ai_confidence && (
        <div className="mt-6 p-4 rounded-xl bg-blue-500/5 border border-blue-500/20 flex items-center gap-3 fade-up">
          <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center shrink-0">
            <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-blue-400">AI Confidence Score: {(ncr.ai_confidence * 100).toFixed(0)}%</p>
            <p className="text-xs text-muted-foreground mt-0.5">This NCR was automatically drafted by ProjectPulse AI. Always verify against original documents before approval.</p>
          </div>
        </div>
      )}
    </div>
  );
}
