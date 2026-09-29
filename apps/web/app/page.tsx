"use client";

import { FormEvent, useEffect, useState } from "react";

type Deal = {
  id: string; name: string; status: string; created_at: string;
  property: { id: string; address?: string | null; city?: string | null; asset_type?: string | null; area_value?: number | null; area_unit?: string | null };
};

const apiBase = process.env.NEXT_PUBLIC_RETHOS_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    try {
      const response = await fetch(`${apiBase}/api/v1/deals`, { cache: "no-store" });
      if (!response.ok) throw new Error("API unavailable. Start the FastAPI app on port 8000.");
      setDeals(await response.json());
      setError("");
    } catch (e) { setError(e instanceof Error ? e.message : "Could not load deals."); }
  }

  useEffect(() => { void refresh(); }, []);

  async function createDeal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const area = String(form.get("area") ?? "").trim();
    const payload = {
      name: String(form.get("name") ?? "").trim(),
      property: {
        address: String(form.get("address") ?? "").trim() || null,
        city: String(form.get("city") ?? "").trim() || null,
        asset_type: String(form.get("asset_type") ?? "").trim() || null,
        area_value: area ? Number(area) : null,
        area_unit: area ? String(form.get("area_unit")) : null,
      },
    };
    try {
      const response = await fetch(`${apiBase}/api/v1/deals`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      if (!response.ok) throw new Error("Deal could not be created. Check the inputs and API.");
      formElement.reset(); await refresh();
    } catch (e) { setError(e instanceof Error ? e.message : "Could not create deal."); }
    finally { setBusy(false); }
  }

  return <main style={{ maxWidth: 1120, margin: "0 auto", padding: "48px 24px" }}>
    <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 42 }}>
      <div><div style={{ fontWeight: 800, letterSpacing: 3, fontSize: 13 }}>RETHOS</div><h1 style={{ fontSize: 34, margin: "12px 0 6px" }}>Deal workspace</h1><p style={{ color: "#617067", margin: 0 }}>Start with the asset. Build the investment case from evidence.</p></div>
      <span style={{ background: "#e4ede5", color: "#315d43", padding: "9px 13px", borderRadius: 20, fontSize: 12 }}>EARLY BUILD · LOCAL SCAFFOLD</span>
    </header>
    <section style={{ display: "grid", gridTemplateColumns: "minmax(280px, 0.8fr) 1.2fr", gap: 22 }}>
      <form onSubmit={createDeal} style={card}>
        <h2 style={h2}>Create a deal</h2><p style={sub}>Create the deal and its first property record.</p>
        <label style={label}>Deal name<input required name="name" placeholder="e.g. Pune residential acquisition" style={input} /></label>
        <label style={label}>Property address<input name="address" placeholder="Street / project (optional)" style={input} /></label>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <label style={label}>City<input name="city" placeholder="City" style={input} /></label>
          <label style={label}>Asset type<input name="asset_type" placeholder="Residential, office…" style={input} /></label>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 110px", gap: 12 }}>
          <label style={label}>Area<input name="area" type="number" min="0.01" step="any" placeholder="Optional" style={input} /></label>
          <label style={label}>Unit<select name="area_unit" defaultValue="sqft" style={input}><option value="sqft">sq ft</option><option value="sqm">sq m</option><option value="acre">acre</option></select></label>
        </div>
        <button disabled={busy} style={button}>{busy ? "Saving…" : "Create deal →"}</button>
        {error && <p role="alert" style={{ color: "#9c342a", fontSize: 13 }}>{error}</p>}
      </form>
      <section style={card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}><h2 style={h2}>Your deals</h2><span style={sub}>{deals.length} total</span></div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(8, minmax(0, 1fr))", gap: 5, margin: "18px 0 22px" }}>
          {["Deal", "Property", "10–20 comps", "Comparable Engine", "Valuation", "Finance", "Max price", "Scenario → Memo"].map((step, i) => <div key={step} title={step} style={{ background: i === 0 || i === 1 ? "#315d43" : "#e9ece8", color: i < 2 ? "white" : "#69766e", borderRadius: 5, padding: "9px 4px", fontSize: 10, textAlign: "center", minHeight: 38 }}>{step}</div>)}
        </div>
        {deals.length === 0 ? <div style={{ border: "1px dashed #cbd3cd", borderRadius: 10, padding: 30, color: "#68766d", textAlign: "center" }}>No deals yet. Create one to start your first underwriting case.</div> : <div style={{ display: "grid", gap: 10 }}>{deals.map(deal => <article key={deal.id} style={{ border: "1px solid #e2e7e2", borderRadius: 10, padding: 16, display: "flex", justifyContent: "space-between", gap: 16 }}><div><strong>{deal.name}</strong><div style={{ color: "#68766d", marginTop: 6, fontSize: 13 }}>{[deal.property.asset_type, deal.property.city, deal.property.address, deal.property.area_value ? `${deal.property.area_value} ${deal.property.area_unit}` : null].filter(Boolean).join(" · ") || "Property details not entered"}</div></div><span style={{ color: "#315d43", fontSize: 12, textTransform: "uppercase" }}>{deal.status}</span></article>)}</div>}
      </section>
    </section>
    <p style={{ color: "#78847c", fontSize: 12, marginTop: 20 }}>Initial slice only. Deal records currently live in API memory and reset when the server restarts; no market data or valuation is implied.</p>
  </main>;
}

const card: React.CSSProperties = { background: "white", border: "1px solid #e5e9e4", borderRadius: 14, padding: 24, boxShadow: "0 8px 24px #17231d08" };
const h2: React.CSSProperties = { fontSize: 19, margin: "0 0 6px" };
const sub: React.CSSProperties = { color: "#68766d", fontSize: 13, margin: "0 0 20px" };
const label: React.CSSProperties = { display: "grid", gap: 7, fontSize: 12, color: "#49594e", marginBottom: 14 };
const input: React.CSSProperties = { width: "100%", border: "1px solid #d8dfd9", borderRadius: 7, padding: "10px 11px", background: "white", color: "#17231d" };
const button: React.CSSProperties = { width: "100%", border: 0, borderRadius: 8, background: "#315d43", color: "white", fontWeight: 700, padding: 12, cursor: "pointer", marginTop: 5 };
