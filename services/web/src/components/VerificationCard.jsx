// Panel "Weryfikacja materialu": prawdziwy zrzut reklamy (GET /documents/{id}/screenshot), metadane,
// wykryte ryzyka i decyzja analityka (PATCH review: true_positive / false_positive).
import { useState } from "react";
import { RiskBadge } from "./ui.jsx";
import MediaPreview from "./MediaPreview.jsx";
import { adRef } from "../lib/caption.js";
import { fmtDate, publisherName, sourceLabel } from "../lib/labels.js";
import { num } from "../lib/ui.js";


/**
 * finding: wynik z API. actionHref/onAction: "Otworz i ocen". compact: uklad pionowy do prawej kolumny.
 * onReview(id, label, note): szybka decyzja (bez niej przyciskow decyzji nie ma). pager: przegladanie kolejki.
 */
export default function VerificationCard({ finding: f, actionHref, onAction, onReview, pager, compact, twin = -1 }) {
  const [busy, setBusy] = useState(false);
  const failed = (f.rule_results || []).filter((r) => r.verdict === "fail")
    .sort((a, b) => (b.severity ?? 0) - (a.severity ?? 0));
  const doc = f.document || {};
  const decide = async (label, text) => {
    if (!window.confirm(`${text}: „${doc.title || "materiał"}”?`)) return;
    setBusy(true);
    try {
      await onReview(f.id, label, null);
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className={`panel verify-card ${compact ? "verify-card--compact" : ""}`} aria-label="Weryfikacja materiału">
      <div className="verify-head">
        <h2>Weryfikacja materiału</h2>
        {pager && pager.total > 1 && (
          <div className="verify-pager">
            <button type="button" className="button ghost small" onClick={pager.prev} aria-label="Poprzedni materiał">‹</button>
            <span className="quiet">{pager.index + 1} z {pager.total}</span>
            <button type="button" className="button ghost small" onClick={pager.next} aria-label="Następny materiał">›</button>
          </div>
        )}
      </div>
      <div className="verify-body">
        <MediaPreview finding={f} />
        <div className="verify-meta">
          <p className="verify-title">{doc.title || "Bez tytułu"}</p>
          {adRef(doc) && <p className="verify-ref quiet mono">{adRef(doc).kind} nr {adRef(doc).id}</p>}
          {twin >= 0 && (
            <p className="verify-twin">Ten sam nadawca i tytuł co pozycja {twin + 1} w kolejce: osobna reklama (inny numer), oceniana oddzielnie.</p>
          )}
          <p className="verify-line">
            <RiskBadge level={f.risk_level} /> <span className="mono">{num(f.risk_score)}</span>
            <span className="quiet"> · {sourceLabel(doc.source)} · {publisherName(doc) || "—"} · {fmtDate(f.created_at)}</span>
          </p>
          {failed.length ? (
            <ul className="verify-risks">
              {failed.slice(0, compact ? 3 : 5).map((r) => (
                <li key={r.rule_id}><strong>{r.rule_name}</strong><span>{r.legal_basis || ""}</span></li>
              ))}
            </ul>
          ) : <p className="muted-copy">Analizator nie wykazał naruszeń reguł.</p>}
          <div className="verify-actions">
            {onReview && (
              <>
                <button type="button" className="button danger-solid" disabled={busy}
                  onClick={() => decide("true_positive", "Potwierdzić naruszenie")}>Potwierdź naruszenie</button>
                <button type="button" className="button secondary" disabled={busy}
                  onClick={() => decide("false_positive", "Odrzucić jako fałszywy alarm")}>Odrzuć</button>
              </>
            )}
            <a className="button ghost" href={actionHref}
              onClick={onAction ? (e) => { e.preventDefault(); onAction(); } : undefined}>Otwórz i oceń</a>
          </div>
        </div>
      </div>
    </section>
  );
}
