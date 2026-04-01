"use client";

import { useCallback, useRef, useState } from "react";

interface ResumeUploadProps {
  onUpload: (file: File) => void;
  disabled?: boolean;
}

export default function ResumeUpload({ onUpload, disabled }: ResumeUploadProps) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      const allowed = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      ];
      if (!allowed.includes(file.type)) {
        alert("Only PDF and DOCX files are supported.");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        alert("File too large. Maximum 10MB.");
        return;
      }
      onUpload(file);
    },
    [onUpload]
  );

  return (
    <div
      className={`relative border-2 border-dashed rounded-xl p-14 flex flex-col items-center justify-center gap-5 transition-all cursor-pointer overflow-hidden ${
        dragOver
          ? "border-primary bg-primary/5"
          : "border-primary/30 bg-surface-container/50 hover:border-primary hover:bg-primary/5"
      } ${disabled ? "opacity-50 pointer-events-none" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
      }}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
      <div className="w-20 h-20 rounded-full bg-surface shadow-soft flex items-center justify-center text-primary">
        <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m6.75 12-3-3m0 0-3 3m3-3v6m-1.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
        </svg>
      </div>
      <div className="text-center">
        <p className="font-headline font-extrabold text-xl text-on-surface">
          Drop Resume Here
        </p>
        <p className="font-body text-xs text-on-surface-variant mt-2">
          Support for PDF, DOCX (Max 10MB)
        </p>
      </div>
      <button
        type="button"
        className="mt-2 px-8 py-3 bg-primary text-white font-headline font-bold text-sm uppercase tracking-wide rounded-lg shadow-soft hover:bg-primary-hover active:scale-95 transition-all"
      >
        Select File
      </button>
    </div>
  );
}
