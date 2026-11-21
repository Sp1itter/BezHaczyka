export default function Panel({ title, actions, children, className = "" }) {
  return (
    <section className={`panel ${className}`}>
      {(title || actions) && (
        <div className="panel-head">
          <h3>{title}</h3>
          <div>{actions}</div>
        </div>
      )}
      <div className="panel-body">{children}</div>
    </section>
  );
}
