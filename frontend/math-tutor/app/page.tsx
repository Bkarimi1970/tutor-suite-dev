"use client";

import { useMemo, useState } from "react";

type TutorReply = {
  final_answer?: string;
  steps?: string[];
  check?: string;
  next_practice?: string[];
  detected_topic?: string;
  level_used?: string;
  method?: string;
  error?: string;
  hint?: string;
};

export default function Page() {
  const [level, setLevel] = useState<"beginner" | "intermediate" | "advanced">("beginner");
  const [q, setQ] = useState("");
  const [out, setOut] = useState<TutorReply | null>(null);
  const [loading, setLoading] = useState(false);

  const canAsk = useMemo(() => q.trim().length > 0 && !loading, [q, loading]);

  async function ask() {
    if (!q.trim() || loading) return;
    setLoading(true);
    setOut(null);

    try {
      const res = await fetch("/api/tutor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: q, level }),
      });
      const data = (await res.json()) as TutorReply;
      setOut(data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 920, margin: "0 auto", padding: 18 }}>
      <h1 style={{ fontSize: 30, fontWeight: 800 }}>Math Tutor App</h1>
      <p style={{ opacity: 0.8, marginTop: 6 }}>
        Type an equation like <code>2*x + 3 = 7</code> or <code>x**2 - 4 = 0</code>.
      </p>

      <div style={{ marginTop: 14, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
          Level
          <select value={level} onChange={(e) => setLevel(e.target.value as any)}>
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </label>

        <div style={{ flex: 1, minWidth: 260, display: "flex", gap: 10 }}>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder='e.g. x**2 - 7*x + 12 = 0'
            style={{ flex: 1, padding: 10, border: "1px solid #ccc", borderRadius: 10 }}
            onKeyDown={(e) => e.key === "Enter" && ask()}
          />
          <button
            onClick={ask}
            disabled={!canAsk}
            style={{
              padding: "10px 14px",
              borderRadius: 10,
              border: "1px solid #ccc",
              cursor: canAsk ? "pointer" : "not-allowed",
            }}
          >
            {loading ? "Thinking..." : "Ask"}
          </button>
        </div>
      </div>

      <section style={{ marginTop: 18 }}>
        {!out ? (
          <div style={{ padding: 14, border: "1px solid #e2e2e2", borderRadius: 12, opacity: 0.8 }}>
            Ask a question to see the solution steps.
          </div>
        ) : out.error ? (
          <div style={{ padding: 14, border: "1px solid #f0c0c0", borderRadius: 12 }}>
            <div style={{ fontWeight: 700 }}>I couldn’t solve that.</div>
            <div style={{ marginTop: 8, whiteSpace: "pre-wrap" }}>{out.error}</div>
            {out.hint ? <div style={{ marginTop: 8, opacity: 0.85 }}>{out.hint}</div> : null}
          </div>
        ) : (
          <div style={{ padding: 16, border: "1px solid #e2e2e2", borderRadius: 12 }}>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "baseline" }}>
              <div style={{ fontSize: 20, fontWeight: 800 }}>{out.final_answer}</div>
              {out.detected_topic ? (
                <span style={{ opacity: 0.75 }}>• {out.detected_topic}</span>
              ) : null}
              {out.level_used ? <span style={{ opacity: 0.75 }}>• Level: {out.level_used}</span> : null}
              {out.method ? <span style={{ opacity: 0.75 }}>• Method: {out.method}</span> : null}
            </div>

            {out.steps?.length ? (
              <div style={{ marginTop: 14 }}>
                <div style={{ fontWeight: 800, marginBottom: 6 }}>Steps</div>
                <ol style={{ margin: 0, paddingLeft: 18 }}>
                  {out.steps.map((s, i) => (
                    <li key={i} style={{ marginBottom: 6 }}>
                      {s}
                    </li>
                  ))}
                </ol>
              </div>
            ) : null}

            {out.check ? (
              <div style={{ marginTop: 12 }}>
                <div style={{ fontWeight: 800, marginBottom: 6 }}>Check</div>
                <div style={{ opacity: 0.9 }}>{out.check}</div>
              </div>
            ) : null}

            {out.next_practice?.length ? (
              <div style={{ marginTop: 12 }}>
                <div style={{ fontWeight: 800, marginBottom: 6 }}>Practice</div>
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {out.next_practice.map((p, i) => (
                    <li key={i}>
                      <code>{p}</code>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        )}
      </section>
    </main>
  );
}
