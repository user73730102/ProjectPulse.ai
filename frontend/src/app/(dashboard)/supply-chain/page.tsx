export default function SupplyChainPage() {
  return (
    <div className="flex flex-col h-full items-center justify-center p-8 text-center fade-up">
      <div className="w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-6">
        <svg className="w-8 h-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.25 18.75a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 01-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 00-3.213-9.193 2.056 2.056 0 00-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 00-10.026 0 1.106 1.106 0 00-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12" />
        </svg>
      </div>
      <h1 className="text-2xl font-bold text-foreground mb-3">Supply Chain Visibility Agent</h1>
      <p className="text-muted-foreground max-w-md mb-8 leading-relaxed">
        This module is currently on our product roadmap. It will provide a geospatial tracking dashboard for long-lead equipment and alert PMs of port congestion or shipping delays.
      </p>
      <div className="px-4 py-2 rounded-full border border-border bg-secondary/50 text-sm text-foreground/80 font-medium">
        Coming in Phase 2
      </div>
    </div>
  );
}
