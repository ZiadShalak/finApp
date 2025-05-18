// src/frontend/src/pages/Watchlists.jsx
import { FaTrash, FaPlus } from "react-icons/fa";
import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../services/api";

export default function Watchlists() {
  const [lists, setLists] = useState([]);
  const [name, setName] = useState("");
  const navigate = useNavigate();

  // Load watchlists on mount
  useEffect(() => {
    api.get("/watchlists")
      .then((r) => setLists(r.data))
      .catch(console.error);
  }, []);

  const create = async () => {
    if (!name.trim()) return;
    try {
      const { data } = await api.post("/watchlists", { name });
      setLists((l) => [...l, data]);
      setName("");
    } catch (err) {
      alert(err.response?.data?.error || "Failed to create");
    }
  };

  const remove = async (id) => {
    if (!window.confirm("Delete this watchlist?")) return;
    try {
      await api.delete(`/watchlists/${id}`);
      setLists((l) => l.filter((w) => w.id !== id));
    } catch (err) {
      alert(err.response?.data?.error || "Failed to delete");
    }
  };

  const logout = () => {
    localStorage.removeItem("JWT");
    navigate("/");
  };

  return (
    <div style={{ padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Your Watchlists</h1>
        <button onClick={logout} style={{ padding: "4px 8px", cursor: "pointer" }}>
          Log out
        </button>
      </div>
      <ul>
        {lists.map((w) => (
          <li key={w.id} style={{ marginBottom: 8 }}>
            <Link to={`/watchlists/${w.id}`} style={{ marginRight: 8 }}>
              {w.name}
            </Link>
            <button
              onClick={() => remove(w.id)}
              style={{
                color: "black",
                // background: "red",
                border: "none",
                padding: "2px 8px",
                cursor: "pointer",
              }}aria-label="Delete watchlist"
            >
              <FaTrash/>
            </button>
          </li>
        ))}
      </ul>
      <div style={{ marginTop: 16 }}>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="New list name"
          style={{ marginRight: 8 }}
        />
        <button onClick={create} aria-label="Add watchlist">
          <FaPlus/>
        </button>
      </div>
    </div>
  );
}
