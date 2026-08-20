"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";

interface ChatMessage {
  role: "user" | "albert";
  content: string;
}

interface AlbertResponse {
  reply: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const MARKETING_ROUTES = ["/", "/privacy", "/terms"];

export function Albert() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [greeted, setGreeted] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const isMarketing = MARKETING_ROUTES.includes(pathname || "/");

  useEffect(() => {
    if (open && !greeted && messages.length === 0) {
      setMessages([
        {
          role: "albert",
          content:
            "Hi, I'm Albert. Ask me anything about building your video ad — adding a client, locking your script, or exporting prompts.",
        },
      ]);
      setGreeted(true);
    }
  }, [open, greeted, messages.length]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (open) {
      const t = setTimeout(() => inputRef.current?.focus(), 300);
      return () => clearTimeout(t);
    }
  }, [open]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    const history = messages.slice(-10).map((m) => ({
      role: m.role === "albert" ? "assistant" : "user",
      content: m.content,
    }));

    try {
      const res = await fetch(`${API_BASE}/api/albert`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, history }),
      });
      if (!res.ok) throw new Error(`Albert API returned ${res.status}`);
      const data: AlbertResponse = await res.json();
      setMessages((prev) => [...prev, { role: "albert", content: data.reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "albert", content: "Sorry, I had trouble connecting. Please try again in a moment." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  if (isMarketing) return null;

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Close Albert" : "Ask Albert for help"}
        className={`
          fixed bottom-6 right-6 z-[9999] flex items-center gap-3
          rounded-full bg-white shadow-lg border border-gray-200
          hover:shadow-xl hover:-translate-y-0.5 active:scale-95
          transition-all duration-200 ease-in-out cursor-pointer
          ${open ? "opacity-0 pointer-events-none scale-90" : "opacity-100 scale-100"}
        `}
        style={{ padding: 0 }}
      >
        <div className="hidden sm:flex items-center gap-3 px-2 py-1">
          <AlbertAvatar size={40} />
          <span className="text-sm font-semibold text-gray-800 pr-2 whitespace-nowrap">
            Need help? Ask Albert
          </span>
        </div>
        <div className="flex sm:hidden p-1">
          <AlbertAvatar size={44} />
        </div>
      </button>

      {/* Chat panel */}
      <div
        className={`
          fixed bottom-6 right-6 z-[9999] flex flex-col
          bg-white rounded-2xl shadow-2xl border border-gray-200
          transition-all duration-300 ease-in-out origin-bottom-right
          ${open ? "opacity-100 scale-100 pointer-events-auto" : "opacity-0 scale-90 pointer-events-none"}
        `}
        style={{ width: "min(360px, calc(100vw - 32px))", maxHeight: "min(520px, calc(100vh - 80px))" }}
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 shrink-0">
          <div className="flex items-center gap-2.5">
            <AlbertAvatar size={32} />
            <span className="text-sm font-bold text-gray-900">Ask Albert</span>
          </div>
          <button
            onClick={() => setOpen(false)}
            aria-label="Close chat"
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors cursor-pointer"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-0">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-2.5 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              {msg.role === "albert" && <AlbertAvatar size={28} />}
              <div
                className={`max-w-[80%] rounded-xl px-3.5 py-2.5 text-sm leading-relaxed ${
                  msg.role === "user" ? "bg-[#0B1C3E] text-white rounded-br-sm" : "bg-gray-100 text-gray-900 rounded-bl-sm"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-2.5 justify-start">
              <AlbertAvatar size={28} />
              <div className="bg-gray-100 text-gray-500 rounded-xl rounded-bl-sm px-3.5 py-2.5 text-sm italic">
                Albert is typing…
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="shrink-0 border-t border-gray-200 px-4 py-3">
          <div className="flex items-center gap-2">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything…"
              disabled={loading}
              className="flex-1 rounded-lg border border-gray-300 bg-gray-50 px-3.5 py-2.5 text-sm text-gray-900 placeholder-gray-400 outline-none focus:border-[#0B1C3E] focus:ring-2 focus:ring-[#0B1C3E]/20 transition-all disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              aria-label="Send message"
              className="shrink-0 w-11 h-11 flex items-center justify-center rounded-lg bg-[#0B1C3E] text-white hover:opacity-90 active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

function AlbertAvatar({ size }: { size: number }) {
  return (
    <div
      className="flex shrink-0 items-center justify-center rounded-full bg-[#0B1C3E] text-white font-bold"
      style={{ width: size, height: size, fontSize: size * 0.42 }}
    >
      A
    </div>
  );
}
