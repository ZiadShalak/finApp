// src/frontend/src/pages/Watchlist.jsx
import { useEffect, useState, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { FaTrash, FaPlus } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

export default function Watchlist() {
  const { id } = useParams();
  const [tickers, setTickers] = useState([]);
  const [symbol, setSymbol] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const wrapperRef = useRef(null);
  const navigate = useNavigate();

  // Load existing watchlist items
  useEffect(() => {
    api.get(`/watchlists/${id}/tickers`)
       .then((r) => {
        // dedupe on symbol
        const uniques = Array.from(
          new Map(r.data.map(item => [item.symbol, item]))
        ).map(([_, val]) => val);
        setTickers(uniques);
      })
       .catch(console.error);
  }, [id]);

  // Fetch suggestions when symbol changes (debounced)
  useEffect(() => {
    if (!symbol) return setSuggestions([]);
    const timer = setTimeout(() => {
      api.get("/tickers", { params: { search: symbol } })
         .then((res) => setSuggestions(res.data))
         .catch(() => setSuggestions([]));
    }, 300);
    return () => clearTimeout(timer);
  }, [symbol]);

  // Close suggestions on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setSuggestions([]);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const add = async (sym = symbol) => {
    const newSymbol = sym.toUpperCase();
    // 1) Prevent duplicates locally
    if (tickers.some((t) => t.symbol === newSymbol)) {
      alert(`"${newSymbol}" is already in your watchlist.`);
      setSymbol("");
      setSuggestions([]);
      return;
    }
    try {
      // 2) Normal add path
      await api.post(`/watchlists/${id}/tickers`, { symbol: newSymbol });
      setTickers(prev => {
        // build a map keyed by symbol to drop duplicates
        const map = new Map(prev.map(item => [item.symbol, item]));
        map.set(newSymbol, { symbol: newSymbol });
        return Array.from(map.values());
     });
      setSymbol("");
      setSuggestions([]);
    } catch (err) {
      console.error("Add ticker error", err);
      alert(err.response?.data?.error || "Failed to add ticker");
      setSymbol("");
      setSuggestions([]);
    }
  };

  const remove = async (sym) => {
    try {
      await api.delete(`/watchlists/${id}/tickers/${sym}`);
      setTickers((t) => t.filter((x) => x.symbol !== sym));
    } catch (err) {
      console.error("Remove ticker error", err);
      alert("Failed to remove ticker");
    }
  };

  return (
    <div>
      <button
        onClick={() => navigate(-1)}
        style={{ marginBottom: 16 }}
      >
        ← Back
      </button>
      <h1>Watchlist {id}</h1>
      <ul>
        {tickers.map((t) => (
            <li key={t.symbol}>
                <Link to={`/tickers/${t.symbol}`} style={{ marginRight: 8 }}>
                    {t.symbol}
                </Link>
                <button onClick={() => remove(t.symbol)} aria-label="Remove ticker">
                    <FaTrash />
                </button>
            </li>
        ))}
      </ul>

      <div ref={wrapperRef} style={{ position: "relative", width: 300 }}>
        <input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          placeholder="Ticker symbol"
          style={{ width: "100%" }}
        />
        <button onClick={() => add()} aria-label="Add ticker">
            <FaPlus />
        </button>

        {suggestions.length > 0 && (
          <ul
            style={{
              position: "absolute",
              top: "100%",
              left: 0,
              right: 0,
              background: "#fff",
              border: "1px solid #ccc",
              listStyle: "none",
              margin: 0,
              padding: 0,
              maxHeight: 200,
              overflowY: "auto",
              zIndex: 10,
            }}
          >
            {suggestions.map((s) => (
              <li
                key={s.symbol}
                style={{ padding: "4px 8px", cursor: "pointer" }}
                onClick={() => add(s.symbol)}
              >
                <strong>{s.symbol}</strong> — {s.name}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
