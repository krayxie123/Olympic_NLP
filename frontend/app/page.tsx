"use client";

import { useState, useCallback } from "react";
import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

function DraggableCard({
  id,
  order,
  onDragStart,
  onDragOver,
  onDrop,
  children,
  label,
}: {
  id: string;
  order: number;
  onDragStart: (id: string) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent, targetId: string) => void;
  children: React.ReactNode;
  label?: string;
}) {
  return (
    <div
      draggable
      onDragStart={() => onDragStart(id)}
      onDragOver={onDragOver}
      onDrop={(e) => onDrop(e, id)}
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: 8,
        padding: 12,
        cursor: "grab",
        background: "#fff",
      }}
      className="draggable-card"
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
        <span style={{ opacity: 0.5, cursor: "grab" }} title="Drag to reorder">⋮⋮</span>
        {label && <span style={{ fontSize: 13, fontWeight: 600 }}>{label}</span>}
      </div>
      {children}
    </div>
  );
}

function DataTable({ data, label }: { data: any[]; label?: string }) {
  const keys = data[0] ? Object.keys(data[0]).filter((k) => typeof data[0][k] !== "object") : [];
  return (
    <div style={{ marginBottom: 16 }}>
      {label && <h4 style={{ marginBottom: 8, opacity: 0.8 }}>{label}</h4>}
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {keys.map((k) => (
              <th key={k} style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: 8 }}>{k}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row: any, i) => (
            <tr key={row.country ?? row.year ?? i}>
              {keys.map((k) => (
                <td key={k} style={{ padding: 8, borderBottom: "1px solid #eee", textAlign: typeof row[k] === "number" ? "right" : "left" }}>{row[k]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Home() {
  const [question, setQuestion] = useState("Top 10 countries by gold in 2008");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [cardOrder, setCardOrder] = useState<string[]>([]);
  const [draggedId, setDraggedId] = useState<string | null>(null);

  const handleDragStart = useCallback((id: string) => {
    setDraggedId(id);
  }, []);
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);
  const handleDrop = useCallback((e: React.DragEvent, targetId: string) => {
    e.preventDefault();
    setDraggedId(null);
    if (!draggedId || draggedId === targetId) return;
    setCardOrder((prev) => {
      const i = prev.indexOf(draggedId);
      const j = prev.indexOf(targetId);
      if (i === -1 || j === -1) return prev;
      const next = [...prev];
      next.splice(i, 1);
      next.splice(j, 0, draggedId);
      return next;
    });
  }, [draggedId]);

  async function runQuery() {
    setLoading(true);
    setResult(null);

    const res = await fetch("http://127.0.0.1:8000/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    const json = await res.json();
    setResult(json);
    if (json && !json.error) {
      const ids: string[] = [];
      if (json.primary?.chart) ids.push("primary");
      (json.secondary || []).forEach((_: any, i: number) => ids.push(`sec-${i}`));
      if (json.primary?.data?.length) ids.push("table-primary");
      (json.secondary || []).forEach((s: any, i: number) => s.data?.length && ids.push(`table-sec-${i}`));
      setCardOrder(ids);
    } else {
      setCardOrder([]);
    }
    setLoading(false);
  }

  return (
    <main style={{ padding: 24, maxWidth: 1000, margin: "0 auto" }}>
      <h1>Olympics Analytics (MVP)</h1>
      <p> Data Disclaimer: Results are recorded at the time of occurrences
        It does not include subsequent corrections from doping violations, bans or reallocations.
      </p>

      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          style={{ flex: 1, padding: 10 }}
        />
        <button onClick={runQuery} style={{ padding: "10px 14px" }}>
          Run
        </button>
      </div>

      {loading && <p style={{ marginTop: 16 }}>Loading...</p>}

      {result?.error && <p style={{ color: "red", marginTop: 16 }}>{result.error}</p>}

      {result && !result.error && (
        <div style={{ marginTop: 24 }}>
          <p><b>Answer:</b> {result.answer}</p>
          <p style={{ fontSize: 12, color: "#666", marginTop: 4 }}>Drag cards to reorder</p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16, marginTop: 16, alignItems: "start" }}>
            {cardOrder.map((id) => {
              if (id === "primary" && (result.primary?.chart || result.chart)) {
                const src = result.primary ?? result;
                return (
                  <div key={id} style={{ gridColumn: "1 / -1" }}>
                    <DraggableCard
                      id={id}
                      order={0}
                      onDragStart={handleDragStart}
                      onDragOver={handleDragOver}
                      onDrop={handleDrop}
                      label="Primary chart"
                    >
                      <Plot
                        key={JSON.stringify(src.data)}
                        data={src.chart?.data ?? []}
                        layout={{ ...src.chart?.layout, autosize: true, height: 420 }}
                        config={{ responsive: true }}
                        style={{ width: "100%", height: 420 }}
                      />
                    </DraggableCard>
                  </div>
                );
              }
              if (id.startsWith("sec-") && result.secondary?.length) {
                const idx = parseInt(id.split("-")[1], 10);
                const sec = result.secondary[idx];
                if (!sec?.chart) return null;
                return (
                  <div key={id}>
                    <DraggableCard
                    key={id}
                    id={id}
                    order={idx}
                    onDragStart={handleDragStart}
                    onDragOver={handleDragOver}
                    onDrop={handleDrop}
                    label={sec.tool_used}
                  >
                    <Plot
                      key={`${id}-${JSON.stringify(sec.data?.slice?.(0, 2))}`}
                      data={sec.chart.data ?? []}
                      layout={{ ...sec.chart.layout, height: 260, autosize: true }}
                      config={{ responsive: true }}
                      style={{ width: "100%", height: 260 }}
                    />
                  </DraggableCard>
                  </div>
                );
              }
              if (id === "table-primary" && ((result.primary?.data ?? result.data)?.length ?? 0) > 0) {
                return (
                  <div key={id}>
                    <DraggableCard
                    key={id}
                    id={id}
                    order={0}
                    onDragStart={handleDragStart}
                    onDragOver={handleDragOver}
                    onDrop={handleDrop}
                    label={result.primary?.tool_used ?? result.tool_used}
                  >
                    <DataTable data={(result.primary?.data ?? result.data) || []} />
                  </DraggableCard>
                  </div>
                );
              }
              if (id.startsWith("table-sec-") && result.secondary?.length) {
                const idx = parseInt(id.split("-")[2], 10);
                const sec = result.secondary[idx];
                if (!sec?.data?.length) return null;
                return (
                  <div key={id}>
                    <DraggableCard
                    key={id}
                    id={id}
                    order={idx}
                    onDragStart={handleDragStart}
                    onDragOver={handleDragOver}
                    onDrop={handleDrop}
                    label={sec.tool_used}
                  >
                    <DataTable data={sec.data} />
                  </DraggableCard>
                  </div>
                );
              }
              return null;
            })}
          </div>
        </div>
      )}
    </main>
  );
}