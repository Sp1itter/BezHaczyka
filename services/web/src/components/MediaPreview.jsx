// Podglad materialu w "Weryfikacji": zawsze cos sensownego, nigdy pusty kafel ani blad przegladarki.
// Kolejnosc: zrzut samej kreacji -> obraz z mediow -> zrzut mobilny -> zrzut desktopowy -> karta tresci.
// Film z magazynu (media/{i}) mozna odtworzyc przyciskiem; wszystko idzie przez API (bez linkow CDN).
import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import { publisherName, sourceLabel } from "../lib/labels.js";
import { isPolish, keyQuote } from "../lib/caption.js";

const VIDEO_SOURCES = ["youtube", "tiktok"];

const base = (id) => `/api/documents/${encodeURIComponent(id)}`;

function candidatesFor(doc) {
  if (!doc) return [];
  const shots = doc.screenshots || {};
  const media = doc.media || [];
  const out = [];
  if (shots.creative) out.push({ key: "creative", src: `${base(doc.id)}/screenshot?viewport=creative` });
  media.forEach((m, i) => { if (m.kind === "image") out.push({ key: `media-${i}`, src: `${base(doc.id)}/media/${i}` }); });
  if (shots.mobile) out.push({ key: "mobile", src: `${base(doc.id)}/screenshot?viewport=mobile` });
  if (shots.desktop) out.push({ key: "desktop", src: `${base(doc.id)}/screenshot?viewport=desktop` });
  return out;
}

function TextCard({ finding }) {
  const doc = finding.document || {};
  const who = publisherName(doc) || sourceLabel(doc.source);
  return (
    <div className="preview-card" role="img" aria-label="Karta treści reklamy (brak obrazu)">
      <div className="preview-card__head">
        <span className="preview-card__avatar" aria-hidden="true">{(who || "?").slice(0, 1).toUpperCase()}</span>
        <span><strong>{who}</strong><small>Sponsorowane · {sourceLabel(doc.source)}</small></span>
      </div>
      {doc.title && <p className="preview-card__title">{doc.title}</p>}
      <p className="preview-card__text">{doc.text_excerpt || "Brak przechwyconej treści."}{doc.text_excerpt?.length >= 400 ? "…" : ""}</p>
      <p className="preview-card__note">Obraz materiału niedostępny: pokazujemy przechwycony tekst reklamy.</p>
    </div>
  );
}

// Wideo (YouTube, TikTok): kadr 16:9 z krotkim napisem zamiast sciany opisu. Kadr z magazynu, gdy scraper
// go zapisal; inaczej ciemne pole z tytulem i kanalem (bez wymyslonych obrazow). Napis = cytat, ktory
// zlapala regula; obcojezyczny oznaczony jako oryginal (tlumaczenie wymaga modelu jezykowego).
function VideoFrame({ finding, src, onError }) {
  const doc = finding.document || {};
  const quote = keyQuote(finding);
  const who = publisherName(doc) || sourceLabel(doc.source);
  return (
    <div className="video-frame" role="img" aria-label={`Kadr materiału wideo: ${doc.title || who}`}>
      {src ? <img src={src} alt="" onError={onError} /> : (
        <div className="video-frame__blank">
          <span className="video-frame__play" aria-hidden="true">▶</span>
          <small>Kadr filmu jeszcze niezapisany</small>
        </div>
      )}
      <div className="video-frame__top"><strong>{doc.title || "Bez tytułu"}</strong><span>{who} · {sourceLabel(doc.source)}</span></div>
      {quote && (
        <p className="video-frame__sub">
          {!isPolish(quote) && <span className="video-frame__lang">oryginał EN</span>}
          {quote}
        </p>
      )}
    </div>
  );
}

export default function MediaPreview({ finding }) {
  const [doc, setDoc] = useState(null);
  const [step, setStep] = useState(0);
  const [video, setVideo] = useState(false);
  const [videoFailed, setVideoFailed] = useState(false);

  useEffect(() => {
    let alive = true;
    setDoc(null); setStep(0); setVideo(false); setVideoFailed(false);
    api.document(finding.document_id)
      .then((d) => { if (alive) setDoc(d || { id: finding.document_id }); })
      .catch(() => { if (alive) setDoc({ id: finding.document_id }); });
    return () => { alive = false; };
  }, [finding.document_id]);

  if (!doc) return <div className="verify-shot verify-shot--empty"><span>Wczytywanie podglądu…</span></div>;
  const list = candidatesFor(doc);
  const videoIndex = (doc.media || []).findIndex((m) => m.kind === "video");
  const hasVideo = videoIndex >= 0 && !videoFailed;
  const current = list[step];

  return (
    <figure className="verify-shot">
      {video && hasVideo ? (
        <video className="preview-video" controls muted playsInline preload="metadata"
          src={`${base(doc.id)}/media/${videoIndex}`} poster={current?.src} onError={() => { setVideoFailed(true); setVideo(false); }} />
      ) : VIDEO_SOURCES.includes(finding.document?.source) ? (
        <VideoFrame finding={finding} src={current?.src} onError={() => setStep((s) => s + 1)} />
      ) : current ? (
        <a href={current.src} target="_blank" rel="noreferrer noopener" title="Otwórz podgląd w pełnym rozmiarze">
          <img src={current.src} alt="Podgląd przechwyconego materiału" onError={() => setStep((s) => s + 1)} />
        </a>
      ) : (
        <TextCard finding={finding} />
      )}
      <figcaption>
        <span>Podgląd przechwyconego materiału</span>
        {hasVideo && (
          <button type="button" className="button ghost small" onClick={() => setVideo((v) => !v)}>
            {video ? "Pokaż kadr" : "Odtwórz film"}
          </button>
        )}
      </figcaption>
    </figure>
  );
}
