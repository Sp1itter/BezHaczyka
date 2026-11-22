import { Component } from "react";

// Blad w jednym widoku nie gasi calego panelu: pokazuje komunikat zamiast czarnego ekranu.
export default class ErrorBoundary extends Component {
  state = { error: null };
  static getDerivedStateFromError(error) { return { error }; }
  componentDidUpdate(prev) { if (prev.resetKey !== this.props.resetKey && this.state.error) this.setState({ error: null }); }
  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="panel"><div className="panel-body empty">
        Nie udało się wyświetlić widoku: {String(this.state.error.message || this.state.error)}
      </div></div>
    );
  }
}
