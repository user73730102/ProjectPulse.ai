"use client";
import { useEffect, useState } from "react";
import { listScheduleRisks, runScheduleAnalysis, ScheduleRisk } from "@/lib/api";

export default function ScheduleRiskPage() {
  const [risks, setRisks] = useState<ScheduleRisk[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = () => {
    setLoading(true);
    listScheduleRisks().then(setRisks).catch(console.error).finally(() => setLoading(false));
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await runScheduleAnalysis();
      alert(`Schedule Analysis Complete! Found ${res.risks_found} critical risks.`);
      fetchData();
    } catch (err: any) {
      alert("Error running schedule analysis: " + err.message);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto pb-24">
      {/* Live Beta Banner */}
      <div className="mb-8 p-4 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-start gap-4 fade-up">
        <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center shrink-0 mt-1">
          <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <h2 className="text-sm font-bold text-purple-400 uppercase tracking-wider mb-1">Live AI Multi-Agent Integration</h2>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-4xl">
            This module is fully hooked up to the backend Schedule Agent. Clicking "Run AI Risk Analysis" will trigger a multi-agent workflow that cross-references critical path tasks with live procurement shipments to generate real AI mitigations!
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between mb-8 fade-up" style={{ animationDelay: "0.1s" }}>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Predictive Schedule Risk Engine</h1>
          <p className="text-sm text-muted-foreground mt-1">Multi-agent analysis of the critical path and resource constraints.</p>
        </div>
        <button 
          onClick={handleSync}
          disabled={syncing}
          className="px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white text-sm font-medium rounded-lg transition-colors shadow-lg shadow-purple-500/20 flex items-center gap-2"
        >
          {syncing ? (
             <>
               <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                 <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                 <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
               </svg>
               Analyzing Schedule...
             </>
          ) : "Run AI Risk Analysis"}
        </button>
      </div>

      {loading ? (
        <div className="space-y-6 fade-up">
          {[1, 2].map(i => <div key={i} className="h-48 bg-card rounded-xl shimmer" />)}
        </div>
      ) : (
        <div className="space-y-6 fade-up" style={{ animationDelay: "0.2s" }}>
          {risks.map((risk) => (
            <div key={risk.id} className="glass rounded-xl p-6 gradient-border">
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-bold text-foreground">{risk.task}</h3>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                      risk.severity === "Critical" ? "badge-critical" : 
                      risk.severity === "Major" ? "badge-major" : "badge-minor"
                    }`}>
                      {risk.severity} Risk
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-4 text-xs font-mono mb-4">
                    <span className="text-muted-foreground bg-secondary/50 px-2 py-1 rounded">Task ID: {risk.id}</span>
                    <span className="text-muted-foreground bg-secondary/50 px-2 py-1 rounded">Driver: {risk.driver}</span>
                    <span className="text-red-400 bg-red-500/10 border border-red-500/20 px-2 py-1 rounded">Impact: {risk.impact}</span>
                  </div>

                  <p className="text-sm text-foreground/80 leading-relaxed mb-6">
                    {risk.description}
                  </p>

                  <div className="bg-secondary/30 rounded-lg p-4 border border-border">
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
                      <svg className="w-4 h-4 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      AI Generated Mitigation Options
                    </h4>
                    <ul className="space-y-2">
                      {risk.mitigations.map((opt, i) => (
                        <li key={i} className="flex items-start gap-3 text-sm text-foreground">
                          <div className="w-5 h-5 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold">
                            {i + 1}
                          </div>
                          {opt}
                        </li>
                      ))}
                      {risk.mitigations.length === 0 && (
                        <li className="text-xs text-muted-foreground italic">No mitigations generated.</li>
                      )}
                    </ul>
                  </div>
                </div>
                
                <div className="shrink-0 flex gap-2 w-full md:w-auto mt-4 md:mt-0">
                  <button className="flex-1 md:flex-none px-4 py-2 bg-secondary hover:bg-secondary/80 text-foreground text-sm font-medium rounded-lg transition-colors">
                    Ignore
                  </button>
                  <button className="flex-1 md:flex-none px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white text-sm font-medium rounded-lg transition-colors shadow-lg shadow-purple-500/20">
                    Apply Mitigation
                  </button>
                </div>
              </div>
            </div>
          ))}
          {risks.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              No critical risks found. Click "Run AI Risk Analysis" to analyze the latest schedule data.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
