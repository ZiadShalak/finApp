// src/frontend/src/App.js
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Watchlists from "./pages/Watchlists";
import Watchlist from "./pages/Watchlist";
import TickerDetail from "./pages/TickerDetail";

function PrivateRoute({ children }) {
  const token = localStorage.getItem("JWT");
  return token ? children : <Navigate to="/" />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/watchlists" element={<PrivateRoute><Watchlists /></PrivateRoute>} />
        <Route path="/watchlists/:id" element={<PrivateRoute><Watchlist /></PrivateRoute>} />
        <Route path="/tickers/:symbol" element={<PrivateRoute><TickerDetail /></PrivateRoute>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
