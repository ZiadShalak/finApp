// src/frontend/src/pages/TickerDetail.jsx
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import api from "../services/api";

export default function TickerDetail() {
  const { symbol } = useParams();
  const [basic, setBasic] = useState(null);
  const [news,  setNews]  = useState(null);
  const [ind,   setInd]   = useState(null);
  const [chart, setChart] = useState(null);

  useEffect(() => {
    // 1) Load the header info immediately
    api.get(`/tickers/${symbol}/basic`)
       .then(r => setBasic(r.data))
       .catch(console.error);

    // 2) In parallel load the panels
    api.get(`/tickers/${symbol}/news`)
       .then(r => setNews(r.data))
       .catch(console.error);

    api.get(`/tickers/${symbol}/indicators`)
       .then(r => setInd(r.data))
       .catch(console.error);

    api.get(`/tickers/${symbol}/chart`)
       .then(r => setChart(r.data))
       .catch(console.error);
  }, [symbol]);

  if (!basic) {
    return <div>Loading header…</div>;
  }

  return (
    <div style={{ padding: 16 }}>
      <h1>{basic.name} ({basic.symbol})</h1>
      <p><strong>Sector:</strong> {basic.sector || "—"}</p>
      <p><strong>Industry:</strong> {basic.industry || "—"}</p>
      <p><strong>Market Cap:</strong> {basic.market_cap?.toLocaleString() || "—"}</p>
      <p><strong>Currency:</strong> {basic.currency || "—"}</p>
      <p><strong>Employees:</strong> {basic.full_time_employees?.toLocaleString() || "—"}</p>
      <p>
        <strong>Website:</strong>{" "}
        {basic.website
          ? <a href={basic.website}
               target="_blank"
               rel="noopener noreferrer">
              {basic.website}
            </a>
          : "—"
        }
      </p>
      <p><strong>Summary:</strong> {basic.long_business_summary || "—"}</p>
      <p><strong>P/E (TTM):</strong> {basic.trailing_pe ?? "—"}</p>

      <div style={{ marginTop: 32 }}>
            <h2>Price & Volume</h2>
          {chart
            ? (
              <LineChart
                width={800}         // ← give it some pixels
                height={300}        // ← give it some pixels
                data={chart.dates.map((date,i) => ({
                  date,
                  close:  chart.closes[i],
                  volume: chart.volumes[i],
                }))}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid stroke="#eee" />
                <XAxis dataKey="date" />
                <YAxis yAxisId="left" domain={["dataMin","dataMax"]}/>
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Line yAxisId="left"  type="monotone" dataKey="close"  stroke="#8884d8" />
                <Line yAxisId="right" type="monotone" dataKey="volume" stroke="#82ca9d" />
              </LineChart>
            )
            : <div>Loading chart…</div>
          }
      </div>

      <section style={{ marginTop: 32 }}>
        <h2>Key Indicators</h2>
        {ind
          ? (
            <ul>
              <li>RSI: {ind.rsi ?? "—"}</li>
              <li>MACD: {ind.macd ?? "—"}</li>
              <li>Piotroski F-Score: {ind.piotroski_score ?? "—"}</li>
            </ul>
          )
          : <div>Loading indicators…</div>
        }
      </section>

      <section style={{ marginTop: 32 }}>
        <h2>Recent News</h2>
        {news
          ? (
            <ul>
              {news.map((art,i) => (
                <li key={i}>
                  <a href={art.url}
                     target="_blank"
                     rel="noopener noreferrer">
                    {art.title}
                  </a>{" "}
                  <small>— {new Date(art.published_at).toLocaleDateString()}</small>
                </li>
              ))}
            </ul>
          )
          : <div>Loading news…</div>
        }
      </section>
    </div>
  );
}
