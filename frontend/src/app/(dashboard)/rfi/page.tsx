"use client";
import { useState, useRef, useEffect } from "react";
import { queryRFI, getRFIHistory, RFIHistoryItem, Citation } from "@/lib/api";

function CitationBadge({ citation, index }: { citation: Citation; index: number }) {
  const fileUrl = citation.file_path 
    ? `http://localhost:8000/${citation.file_path}${citation.page ? `#page=${citation.page}` : ''}`
    : null;

  return (
    <div className="mt-2 p-3 rounded-lg bg-secondary/30 border border-border/50 text-xs">
      <div className="flex items-center gap-2 mb-1.5">
        <span className="font-mono text-[10px] bg-secondary px-1.5 py-0.5 rounded text-muted-foreground shrink-0">
          [SOURCE {index + 1}]
        </span>
        
        {fileUrl ? (
          <a 
            href={fileUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-blue-400 hover:text-blue-300 hover:underline truncate transition-colors flex items-center gap-1"
          >
            {citation.document_name || "Unknown Document"}
            <svg className="w-3 h-3 opacity-70 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        ) : (
          <span className="font-semibold text-foreground truncate">
            {citation.document_name || "Unknown Document"}
          </span>
        )}

        {citation.page && (
          <span className="text-muted-foreground shrink-0">· Page {citation.page}</span>
        )}
      </div>
      <div className="flex gap-2">
        <div className="w-0.5 bg-blue-500/50 rounded-full shrink-0" />
        <p className="text-muted-foreground italic line-clamp-3">
          "{citation.excerpt}"
        </p>
      </div>
    </div>
  );
}

export default function RFIPage() {
  const [history, setHistory] = useState<RFIHistoryItem[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getRFIHistory(10).then(data => setHistory(data.reverse())).catch(console.error);
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, loading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const currentQ = question;
    setQuestion("");
    setLoading(true);

    // Optimistic UI update
    const tempId = Date.now();
    setHistory(prev => [...prev, { id: tempId, question: currentQ, answer: null, citations: null, created_at: new Date().toISOString() }]);

    try {
      const res = await queryRFI(currentQ);
      setHistory(prev => prev.map(item => item.id === tempId ? {
        id: res.entry_id || tempId,
        question: res.question,
        answer: res.answer,
        citations: res.citations,
        created_at: new Date().toISOString()
      } : item));
    } catch (err: any) {
      setHistory(prev => prev.map(item => item.id === tempId ? { ...item, answer: `Error: ${err.message}` } : item));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="px-6 py-4 border-b border-border glass sticky top-0 z-10 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-foreground flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.25 9V5.25A2.25 2.25 0 0110.5 3h6a2.25 2.25 0 012.25 2.25v13.5A2.25 2.25 0 0116.5 21h-6a2.25 2.25 0 01-2.25-2.25V15M12 9l3 3m0 0l-3 3m3-3H2.25" />
            </svg>
            RFI Assistant
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">Ask questions about project specifications and non-conformances.</p>
        </div>
        <div className="px-2.5 py-1 rounded bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-bold tracking-wider">
          Llama 3 Powered
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {history.length === 0 && !loading && (
          <div className="h-full flex flex-col items-center justify-center text-center opacity-50">
            <svg className="w-12 h-12 text-muted-foreground mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p className="text-sm">No RFI history yet.</p>
            <p className="text-xs text-muted-foreground mt-1">Try asking: "Why was the UPS submittal rejected?"</p>
          </div>
        )}

        {history.map((item) => (
          <div key={item.id} className="space-y-4 fade-up">
            {/* User Question */}
            <div className="flex justify-end">
              <div className="max-w-[80%] chat-user px-4 py-3 shadow-sm">
                <p className="text-sm text-foreground">{item.question}</p>
              </div>
            </div>

            {/* AI Answer */}
            <div className="flex justify-start">
              <div className="max-w-[85%] chat-ai p-5 shadow-md">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-6 h-6 rounded bg-blue-500/20 flex items-center justify-center">
                    <svg className="w-3.5 h-3.5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <span className="text-xs font-bold text-foreground">ProjectPulse AI</span>
                </div>

                {!item.answer ? (
                  <div className="space-y-2">
                    <div className="h-4 bg-secondary rounded w-3/4 shimmer" />
                    <div className="h-4 bg-secondary rounded w-1/2 shimmer" />
                  </div>
                ) : (
                  <>
                    <div className="text-sm text-foreground/90 whitespace-pre-wrap leading-relaxed">
                      {item.answer}
                    </div>
                    {item.citations && item.citations.length > 0 && (
                      <div className="mt-5 pt-4 border-t border-border">
                        <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2">Sources Referenced</p>
                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-2">
                          {item.citations.map((c, i) => (
                            <CitationBadge key={i} citation={c} index={i} />
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start fade-up">
            <div className="chat-ai px-5 py-4 flex items-center gap-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full pulse-glow" />
              <div className="w-2 h-2 bg-purple-500 rounded-full pulse-glow" style={{ animationDelay: "0.2s" }} />
              <div className="w-2 h-2 bg-blue-500 rounded-full pulse-glow" style={{ animationDelay: "0.4s" }} />
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-background border-t border-border">
        <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about the project specifications..."
            className="w-full bg-secondary border border-border text-foreground rounded-xl pl-5 pr-14 py-4 focus:outline-none focus:ring-2 focus:ring-blue-500/50 shadow-sm"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!question.trim() || loading}
            className="absolute right-2 top-2 bottom-2 aspect-square flex items-center justify-center bg-blue-600 hover:bg-blue-500 disabled:bg-secondary disabled:text-muted-foreground text-white rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}
