"use client";
import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { listSubmittals, Submittal, runComplianceCheck, uploadSubmittal } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    pending: { label: "Pending", cls: "bg-slate-500/10 text-slate-400 border-slate-500/20" },
    under_review: { label: "Under Review", cls: "bg-amber-500/10 text-amber-500 border-amber-500/20" },
    approved: { label: "Approved", cls: "badge-approved" },
    rejected: { label: "Rejected", cls: "bg-red-500/10 text-red-500 border-red-500/20" },
  };
  const s = map[status] || map.pending;
  return <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${s.cls}`}>{s.label}</span>;
}

export default function SubmittalsPage() {
  const [submittals, setSubmittals] = useState<Submittal[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningId, setRunningId] = useState<number | null>(null);
  const [uploading, setUploading] = useState(false);
  const { user } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = () => {
    setLoading(true);
    listSubmittals().then(setSubmittals).catch(console.error).finally(() => setLoading(false));
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.type !== "application/pdf") {
      toast.error("Please upload a PDF file.");
      return;
    }

    setUploading(true);
    try {
      await uploadSubmittal(file);
      toast.success("Submittal uploaded successfully.");
      fetchData(); // Refresh list to show the new parsed submittal
    } catch (err: any) {
      toast.error(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleRunCompliance = async (id: number) => {
    setRunningId(id);
    try {
      const res = await runComplianceCheck(id);
      if (res.error) {
        toast.error("Compliance check failed: " + res.error);
      } else {
        toast.success(`Compliance check complete. ${res.ncrs_created} NCR(s) generated.`);
        fetchData();
      }
    } catch (err: any) {
      toast.error("Error: " + err.message);
    } finally {
      setRunningId(null);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto pb-24">
      <div className="flex items-center justify-between mb-8 fade-up">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z" />
            </svg>
            Vendor Submittals
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Upload vendor cut-sheets and run AI compliance checks against project specs.</p>
        </div>
        
        {(user?.role === "contractor" || user?.role === "engineer" || user?.role === "pm") && (
          <div>
            <input 
              type="file" 
              accept=".pdf" 
              className="hidden" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
            />
            <button 
              onClick={handleUploadClick}
              disabled={uploading}
              className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50 shadow-lg shadow-emerald-500/20"
            >
              {uploading ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Uploading & Parsing...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                  </svg>
                  Upload Submittal
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => <div key={i} className="h-20 bg-card rounded-xl shimmer" />)}
        </div>
      ) : (
        <div className="glass rounded-xl overflow-hidden fade-up gradient-border">
          <table className="w-full text-left text-sm">
            <thead className="bg-secondary/50 border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-6 py-4 font-medium">Submittal No.</th>
                <th className="px-6 py-4 font-medium">Title & Vendor</th>
                <th className="px-6 py-4 font-medium">Spec Ref</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {submittals.map(sub => (
                <tr key={sub.id} className="hover:bg-secondary/30 transition-colors group">
                  <td className="px-6 py-4">
                    <span className="font-mono text-xs font-semibold text-foreground">{sub.submittal_number}</span>
                  </td>
                  <td className="px-6 py-4">
                    <p className="font-medium text-foreground">{sub.title}</p>
                    <p className="text-xs text-muted-foreground">{sub.vendor_name || "Unknown vendor"}</p>
                  </td>
                  <td className="px-6 py-4">
                    <span className="font-mono text-xs text-muted-foreground bg-secondary px-2 py-1 rounded">
                      {sub.spec_section_ref || "N/A"}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={sub.status} />
                  </td>
                  <td className="px-6 py-4 text-right space-x-3">
                    {(user?.role === "engineer" || user?.role === "pm" || user?.role === "auditor") && sub.status === "pending" && (
                      <button
                        onClick={() => handleRunCompliance(sub.id)}
                        disabled={runningId === sub.id}
                        className="px-3 py-1.5 rounded bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 text-xs font-medium transition-colors disabled:opacity-50"
                      >
                        {runningId === sub.id ? "Running AI..." : "Run AI Check"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {submittals.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground">
                    No submittals found. Upload a submittal to get started.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
