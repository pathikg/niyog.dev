"use client";

import { useRef, useState } from "react";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import ChatMessage from "@/components/chat-message";
import ResumeUpload from "@/components/resume-upload";
import ProfileSidebar from "@/components/profile-sidebar";

type Phase = "upload" | "extracting" | "reviewing" | "gap_filling" | "complete";

interface Message {
  role: "assistant" | "user";
  content: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function OnboardPage() {
  const [phase, setPhase] = useState<Phase>("upload");
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello, I'm Niyog. Let's build your professional profile. To begin mapping your career journey, please upload your resume below.",
    },
  ]);
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null);
  const [uploading, setUploading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [chatInput, setChatInput] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);
  const streamStartedRef = useRef(false);

  function scrollToBottom() {
    setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
  }

  async function handleUpload(file: File) {
    setUploading(true);
    setPhase("extracting");
    setStatusText("Reading your resume...");
    streamStartedRef.current = false;
    setMessages((prev) => [
      ...prev,
      { role: "user", content: `Uploading ${file.name}...` },
    ]);
    scrollToBottom();

    const token = localStorage.getItem("token");
    const formData = new FormData();
    formData.append("file", file);

    try {
      await fetchEventSource(`${API_BASE}/api/candidates/resume`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
        openWhenHidden: true, // Keep streaming even if tab is hidden

        onopen: async (response) => {
          if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `Upload failed: ${response.status}`);
          }
        },

        onmessage: (event) => {
          const data = JSON.parse(event.data);

          switch (event.event) {
            case "status":
              setStatusText(data.message);
              break;

            case "error":
              throw new Error(data.message);

            case "extracted":
              // Profile data received — update sidebar, keep spinner until tokens flow
              setProfile(data.profile_attributes);
              setStatusText("Preparing your profile summary...");
              break;

            case "token":
              // Real LLM token — render immediately
              if (!streamStartedRef.current) {
                streamStartedRef.current = true;
                setPhase("reviewing");
                setStreaming(true);
                setStatusText("");
                setMessages((prev) => [
                  ...prev,
                  { role: "assistant", content: data.text },
                ]);
              } else {
                setMessages((prev) => {
                  const updated = [...prev];
                  const last = updated[updated.length - 1];
                  updated[updated.length - 1] = {
                    ...last,
                    content: last.content + data.text,
                  };
                  return updated;
                });
              }
              scrollToBottom();
              break;

            case "done":
              setStreaming(false);
              setPhase("reviewing");
              scrollToBottom();
              break;
          }
        },

        onerror: (err) => {
          setPhase("upload");
          setStatusText("");
          setStreaming(false);
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: `Something went wrong: ${
                err instanceof Error ? err.message : "Unknown error"
              }. Please try again.`,
            },
          ]);
          scrollToBottom();
          throw err; // Stop retrying
        },

        onclose: () => {
          setUploading(false);
        },
      });
    } catch (err) {
      if (!streamStartedRef.current) {
        // Only show error if we haven't already started streaming
        setPhase("upload");
        setStatusText("");
        setStreaming(false);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Something went wrong: ${
              err instanceof Error ? err.message : "Unknown error"
            }. Please try again.`,
          },
        ]);
        scrollToBottom();
      }
    } finally {
      setUploading(false);
    }
  }

  function handleChatSend() {
    if (!chatInput.trim() || streaming) return;
    const msg = chatInput.trim();
    setChatInput("");
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    scrollToBottom();

    // Phase 1B will wire this to the backend chat endpoint
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Thanks for the feedback! Chat processing will be connected in the next update. Your extracted profile is saved.",
        },
      ]);
      scrollToBottom();
    }, 300);
  }

  return (
    <div className="max-w-7xl mx-auto px-8 pt-12">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
        <h1 className="font-headline font-bold text-sm tracking-widest uppercase text-primary">
          Candidate Onboarding
        </h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <section className="lg:col-span-8 flex flex-col gap-6">
          <div className="bg-surface rounded-xl p-8 border border-outline shadow-card flex flex-col gap-8">
            {messages.map((msg, i) => (
              <ChatMessage key={i} role={msg.role} content={msg.content} />
            ))}

            {phase === "upload" && (
              <div className="ml-16">
                <ResumeUpload onUpload={handleUpload} disabled={uploading} />
              </div>
            )}

            {phase === "extracting" && (
              <div className="flex gap-4 max-w-2xl">
                <div className="flex-shrink-0 w-12 h-12 bg-primary rounded-xl shadow-soft flex items-center justify-center">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                </div>
                <div className="bg-background p-4 rounded-2xl rounded-tl-none border border-outline border-l-4 border-l-primary/30 flex items-center gap-3">
                  <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                  <p className="font-headline font-medium text-sm text-primary">
                    {statusText || "Processing resume..."}
                  </p>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {(phase === "reviewing" || phase === "gap_filling") && (
            <div className="bg-surface border border-outline rounded-xl p-1 shadow-soft flex items-center gap-2 overflow-hidden focus-within:ring-2 focus-within:ring-primary/20 transition-all">
              <input
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleChatSend();
                  }
                }}
                disabled={streaming}
                className="bg-transparent border-none focus:ring-0 focus:outline-none text-on-surface font-body text-[15px] w-full px-5 py-4 placeholder:text-on-surface-variant/40 disabled:opacity-50"
                placeholder={
                  streaming
                    ? "Niyog is typing..."
                    : "Type a correction or say 'looks good' to continue..."
                }
              />
              <button
                onClick={handleChatSend}
                disabled={streaming}
                className="p-4 mr-1 text-primary hover:bg-primary/5 rounded-lg transition-colors disabled:opacity-50"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg>
              </button>
            </div>
          )}
        </section>

        <aside className="lg:col-span-4">
          <ProfileSidebar phase={phase} profile={profile} />
        </aside>
      </div>
    </div>
  );
}
