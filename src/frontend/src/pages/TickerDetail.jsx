// src/frontend/src/pages/TickerDetail.jsx
import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FaArrowLeft } from "react-icons/fa";
import api from "../services/api";

export default function TickerDetail() {
  const { symbol } = useParams();
  const [info, setInfo] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.get(`/tickers/${symbol}`)
       .then(res => setInfo(res.data))
       .catch(console.error);
  }, [symbol]);

  if (!info) return <p>Loading…</p>;

  return (
    <div>
      <button
        onClick={() => navigate(-1)}
        aria-label="Back">
        <FaArrowLeft/>
      </button>
      <h1>{info.name} ({info.symbol})</h1>
      <p><strong>Sector:</strong> {info.sector}</p>
      <p><strong>Market Cap:</strong> {info.market_cap}</p>
      <p><strong>Current Price:</strong> ${info.current_price}</p>
      {/* add more fields as needed */}
    </div>
  );
}
