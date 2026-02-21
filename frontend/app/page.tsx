"use client";

import { useState } from "react";
import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export default function Home() {
  const [question, setQuestion] = useState("Top 10 countries by gold in 2008");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

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
    setLoading(false);
  }

  return (
    <main style={{ padding: 24, maxWidth: 1000, margin: "0 auto" }}>
      <h1>Olympics Analytics (MVP)</h1>

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

      {result && (
        <div style={{ marginTop: 24 }}>
          <p><b>Answer:</b> {result.answer}</p>

          {result.chart && (
            <div style={{ marginTop: 16 }}>
              <Plot
                data={result.chart.data}
                layout={result.chart.layout}
                style={{ width: "100%", height: 520 }}
              />
            </div>
          )}

          {result.data && (
            <div style={{ marginTop: 16 }}>
              <h3>Data</h3>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: 8 }}>Country</th>
                    <th style={{ textAlign: "right", borderBottom: "1px solid #ddd", padding: 8 }}>Medals</th>
                  </tr>
                </thead>
                <tbody>
                  {result.data.map((row: any) => (
                    <tr key={row.country}>
                      <td style={{ padding: 8, borderBottom: "1px solid #eee" }}>{row.country}</td>
                      <td style={{ padding: 8, borderBottom: "1px solid #eee", textAlign: "right" }}>{row.medals}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </main>
  );
}