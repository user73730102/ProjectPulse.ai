"use client";
import { useEffect, useState, useRef } from "react";
import { listDocuments, uploadDocument, deleteDocument, Document } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { user } = useAuth();

  useEffect(() => {
    fetchDocs();
  }, []);

  const fetchDocs = () => {
    setLoading(true);
    listDocuments().then(setDocuments).catch(console.error).finally(() => setLoading(false));
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Are you sure you want to delete ${name}? This will remove all extracted chunks and related submittals.`)) return;
    try {
      await deleteDocument(id);
      toast.success("Document deleted");
      fetchDocs();
    } catch (err: any) {
      toast.error(err.message || "Failed to delete document");
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError("");

    try {
      // Default to "spec" for this demo, in a real app you'd prompt the user
      await uploadDocument(file, "specification");
      toast.success("Document uploaded successfully");
      fetchDocs(); // Refresh list
    } catch (err: any) {
      toast.error(err.message || "Failed to upload document");
      setUploadError(err.message || "Failed to upload document");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8 fade-up">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Project Documents</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage specifications, drawings, and other unstructured data.</p>
        </div>
        {(user?.role === "pm" || user?.role === "engineer") && (
          <div>
            <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" accept=".pdf,.docx,.txt" />
            <button
              onClick={handleUploadClick}
              disabled={uploading}
              className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium transition-colors flex items-center gap-2"
            >
              {uploading ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  Uploading...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  Upload Document
                </>
              )}
            </button>
            {uploadError && <p className="text-xs text-red-400 mt-2 text-right absolute">{uploadError}</p>}
          </div>
        )}
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => <div key={i} className="h-16 bg-card rounded-xl shimmer" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 fade-up">
          {documents.map((doc) => (
            <div key={doc.id} className="glass rounded-xl p-5 hover:border-blue-500/30 transition-all group relative">
              {user?.role === "pm" && (
                <button
                  onClick={() => handleDelete(doc.id, doc.original_name)}
                  className="absolute top-4 right-4 text-red-500/50 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                  title="Delete Document"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              )}
              <div className="flex items-start justify-between mb-3 pr-8">
                <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center shrink-0">
                  <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                </div>
                {doc.is_processed ? (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full border badge-approved">Processed</span>
                ) : (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full border badge-pending animate-pulse">Processing</span>
                )}
              </div>
              <p className="text-sm font-semibold text-foreground truncate" title={doc.original_name}>
                {doc.original_name}
              </p>
              <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                <span className="uppercase tracking-wider font-semibold">{doc.doc_type}</span>
                <span>·</span>
                <span>{doc.page_count ? `${doc.page_count} pages` : 'Unknown pages'}</span>
              </div>
            </div>
          ))}
          {documents.length === 0 && (
            <div className="col-span-full p-12 text-center text-muted-foreground glass rounded-xl border-dashed">
              No documents uploaded yet.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
