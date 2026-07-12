"use client";
import { useEffect, useState } from "react";
import { listShipments, evaluateShipment, Shipment } from "@/lib/api";
import { toast } from "sonner";

export default function SupplyChainPage() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [evaluatingId, setEvaluatingId] = useState<number | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = () => {
    setLoading(true);
    listShipments().then(setShipments).catch(console.error).finally(() => setLoading(false));
  };

  const handleEvaluate = async (id: number) => {
    setEvaluatingId(id);
    try {
      const res = await evaluateShipment(id);
      if (res.risk_flag) {
        toast.error(`AI detected a delay risk: ${res.risk_flag} (+${res.delay} Days)`);
      } else {
        toast.success("Shipment is on track. No delays detected.");
      }
      fetchData();
    } catch (err: any) {
      toast.error("Error evaluating shipment: " + err.message);
    } finally {
      setEvaluatingId(null);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto pb-24">
      {/* Live Beta Banner */}
      <div className="mb-8 p-4 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-start gap-4 fade-up">
        <div className="w-10 h-10 rounded-full bg-orange-500/20 flex items-center justify-center shrink-0 mt-1">
          <svg className="w-5 h-5 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <h2 className="text-sm font-bold text-orange-400 uppercase tracking-wider mb-1">Live AI Agent Integration</h2>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-4xl">
            This module is fully hooked up to the backend Supply Chain Agent. Clicking "AI Risk Scan" will trigger the LLM to analyze the origin, destination, and current location of the shipment to detect port congestion or transit delays!
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between mb-8 fade-up" style={{ animationDelay: "0.1s" }}>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Supply Chain Visibility Agent</h1>
          <p className="text-sm text-muted-foreground mt-1">Live geospatial tracking and procurement risk detection for long-lead equipment.</p>
        </div>
      </div>

      {loading ? (
        <div className="h-64 bg-card rounded-xl shimmer fade-up" />
      ) : (
        <div className="glass rounded-xl overflow-hidden fade-up gradient-border" style={{ animationDelay: "0.2s" }}>
          <table className="w-full text-left text-sm">
            <thead className="bg-secondary/50 border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-6 py-4 font-medium">Shipment & Equipment</th>
                <th className="px-6 py-4 font-medium">Route</th>
                <th className="px-6 py-4 font-medium">Status & Location</th>
                <th className="px-6 py-4 font-medium">ETA</th>
                <th className="px-6 py-4 font-medium text-right">Risk Detection</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {shipments.map(shp => (
                <tr key={shp.id} className="hover:bg-secondary/30 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="font-mono text-xs text-muted-foreground mb-1">{shp.id}</div>
                    <div className="font-bold text-foreground">{shp.equipment}</div>
                    <div className="text-xs text-muted-foreground">{shp.vendor}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col gap-1 text-xs">
                      <span className="text-muted-foreground flex items-center gap-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-border" /> {shp.origin}
                      </span>
                      <div className="w-0.5 h-3 bg-border ml-0.5" />
                      <span className="text-foreground flex items-center gap-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> {shp.destination}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border mb-2 inline-block ${
                      shp.status === "In Transit" ? "bg-blue-500/10 text-blue-400 border-blue-500/20" : 
                      shp.status === "Customs Clearance" ? "bg-amber-500/10 text-amber-500 border-amber-500/20" :
                      "bg-slate-500/10 text-slate-400 border-slate-500/20"
                    }`}>
                      {shp.status}
                    </span>
                    <div className="text-sm font-medium text-foreground flex items-center gap-1.5 mt-1">
                      <svg className="w-3.5 h-3.5 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      {shp.location}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="font-mono text-sm text-foreground">{shp.eta}</span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    {shp.riskFlag ? (
                      <div className="inline-flex flex-col items-end">
                        <span className="text-xs font-bold text-red-400 bg-red-500/10 border border-red-500/20 px-2 py-0.5 rounded">
                          {shp.riskFlag}
                        </span>
                        <span className="text-xs font-mono text-muted-foreground mt-1">
                          Est. Delay: <span className="text-red-400">{shp.delayEstimate}</span>
                        </span>
                      </div>
                    ) : (
                      <button 
                        onClick={() => handleEvaluate(shp.shipment_db_id)}
                        disabled={evaluatingId === shp.shipment_db_id}
                        className="px-3 py-1.5 text-xs font-medium text-orange-400 hover:text-orange-300 transition-colors bg-orange-500/10 border border-orange-500/20 rounded"
                      >
                        {evaluatingId === shp.shipment_db_id ? "Scanning..." : "AI Risk Scan"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {shipments.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground">
                    No shipments found in database.
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
