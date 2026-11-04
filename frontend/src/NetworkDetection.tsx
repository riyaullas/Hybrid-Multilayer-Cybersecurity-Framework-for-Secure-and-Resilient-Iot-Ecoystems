
import { useState } from 'react';
import { Activity, AlertTriangle, ShieldCheck } from 'lucide-react';
import { api } from './services/api';

const features = [
  'Header_Length', 'Protocol Type', 'Duration', 'Rate', 'Srate',
  'Drate', 'fin_flag_number', 'syn_flag_number', 'rst_flag_number',
  'psh_flag_number', 'ack_flag_number', 'ece_flag_number',
  'cwr_flag_number', 'ack_count', 'syn_count', 'fin_count',
  'rst_count', 'HTTP', 'HTTPS', 'DNS', 'Telnet', 'SMTP',
  'SSH', 'IRC', 'TCP', 'UDP', 'DHCP', 'ARP', 'ICMP', 'IGMP',
  'IPv', 'LLC', 'Tot sum', 'Min', 'Max', 'AVG', 'Std',
  'Tot size', 'IAT', 'Number', 'Magnitue', 'Radius',
  'Covariance', 'Variance', 'Weight'
];

export default function NetworkDetection() {
  const [sample, setSample] = useState<Record<string, string>>(
    Object.fromEntries(features.map((feature) => [feature, '0']))
  );
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function analyze() {
    setBusy(true);
    setError('');
    setResult(null);

    try {
      const numericSample = Object.fromEntries(
        features.map((feature) => {
          const value = sample[feature].trim();

          if (value === '' || !Number.isFinite(Number(value))) {
            throw new Error(`Enter a valid numeric value for ${feature}.`);
          }

          return [feature, Number(value)];
        })
      );

      const response = await api('/analysis/network-traffic', {
        method: 'POST',
        body: JSON.stringify({ sample: numericSample })
      });

      setResult(response);
    } catch (e: any) {
      setError(e.message || 'Network traffic analysis failed.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-heading">
        <div>
          <div className="eyebrow">MACHINE LEARNING / NETWORK SECURITY</div>
          <h1>Network Traffic Detection</h1>
          <p>
            Classify a numeric network-flow sample using the trained
            Random Forest model.
          </p>
        </div>
      </div>

      <div className="notice">
        <AlertTriangle size={16} />
        <span>
          Research prototype. Enter values from the same feature definitions
          and units used during training. Zero-filled defaults are placeholders,
          not a real traffic sample.
        </span>
      </div>

      <section className="panel">
        <div className="panel-head">
          <h3>Network flow features ({features.length})</h3>
        </div>

        <div className="feature-form">
          {features.map((feature) => (
            <label key={feature}>
              {feature}
              <input
                type="number"
                step="any"
                value={sample[feature]}
                onChange={(e) =>
                  setSample((previous) => ({
                    ...previous,
                    [feature]: e.target.value
                  }))
                }
              />
            </label>
          ))}
        </div>

        <button className="primary" onClick={analyze} disabled={busy}>
          <Activity size={16} />
          {busy ? 'Analyzing...' : 'Analyze network traffic'}
        </button>
      </section>

      {error && <div className="error-box">{error}</div>}

      {result && (
        <section className="panel">
          <div className="panel-head">
            <h3>Classification result</h3>
          </div>

          <div className="notice">
            {result.classification === 'Benign' ? (
              <ShieldCheck size={20} />
            ) : (
              <AlertTriangle size={20} />
            )}
            <span>
              <b>Prediction: {result.classification}</b>
              <br />
              Model: {result.model}
              <br />
              Features: {result.feature_count}
            </span>
          </div>

          {result.probabilities && (
            <>
              <h3>Model output scores</h3>
              {Object.entries(result.probabilities).map(([label, score]) => (
                <div key={label} className="setting-row">
                  <span>{label}</span>
                  <b>{(Number(score) * 100).toFixed(2)}%</b>
                </div>
              ))}
              <p className="muted">
                These scores are model outputs, not calibrated probabilities
                of a real attack.
              </p>
            </>
          )}

          <p className="muted">{result.warning}</p>
        </section>
      )}
    </div>
  );
}
