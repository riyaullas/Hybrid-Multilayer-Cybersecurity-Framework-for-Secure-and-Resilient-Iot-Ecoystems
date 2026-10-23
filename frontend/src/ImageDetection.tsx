import { useState } from 'react';
import { Image as ImageIcon, Upload, ShieldCheck, AlertTriangle, LoaderCircle } from 'lucide-react';
import { getToken } from './services/api';

const API_BASE =
  import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

type Prediction = {
  prediction: string;
  confidence: number;
  probabilities: Record<string, number>;
  model: string;
  image_size: string;
  note: string;
};

export default function ImageDetection() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [result, setResult] = useState<Prediction | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  function selectFile(next: File | undefined) {
    setResult(null);
    setError('');

    if (preview) URL.revokeObjectURL(preview);
    setPreview('');
    setFile(null);

    if (!next) return;

    if (!['image/png', 'image/jpeg'].includes(next.type)) {
      setError('Please select a PNG or JPEG image.');
      return;
    }

    if (next.size > 2 * 1024 * 1024) {
      setError('The image must be smaller than 2 MB.');
      return;
    }

    const url = URL.createObjectURL(next);
    const img = new Image();

    img.onload = () => {
      if (img.naturalWidth !== 8 || img.naturalHeight !== 8) {
        URL.revokeObjectURL(url);
        setError('Please choose a generated 8×8 traffic-representation image.');
        return;
      }

      setFile(next);
      setPreview(url);
    };

    img.onerror = () => {
      URL.revokeObjectURL(url);
      setError('Could not read this image.');
    };

    img.src = url;
  }

  async function predict() {
    if (!file) return;

    setBusy(true);
    setError('');
    setResult(null);

    try {
      const headers: Record<string, string> = {};
      const token = getToken();
      if (token) headers.Authorization = `Bearer ${token}`;

      const form = new FormData();
      form.append('file', file);

      const response = await fetch(
        `${API_BASE}/image-detection/predict`,
        { method: 'POST', headers, body: form }
      );

      if (!response.ok) {
        let message = `Prediction failed (${response.status})`;
        try {
          const data = await response.json();
          message = data.detail || message;
        } catch {}
        throw new Error(message);
      }

      setResult(await response.json());
    } catch (e: any) {
      setError(e.message || 'Could not run image detection.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-heading">
        <div>
          <div className="eyebrow">DEEP LEARNING / IMAGE CLASSIFICATION</div>
          <h1>Image-Based Detection</h1>
          <p>
            Classify generated network-traffic representations using the
            trained convolutional neural network.
          </p>
        </div>
      </div>

      <div className="notice">
        <ImageIcon size={18} />
        <span>
          This experimental CNN expects an 8×8 grayscale traffic image.
          It does not classify arbitrary photographs. Results are research
          predictions, not proof of a real cyberattack.
        </span>
      </div>

      <section className="panel">
        <div className="panel-head">
          <h3>Select a traffic image</h3>
        </div>

        <label className="field-label">
          PNG or JPEG image (8×8 pixels)
          <input
            type="file"
            accept="image/png,image/jpeg"
            onChange={e => selectFile(e.target.files?.[0])}
          />
        </label>

        {preview && (
          <div style={{ margin: '20px 0' }}>
            <p><b>Image preview</b></p>
            <img
              src={preview}
              alt="Selected traffic representation"
              width={160}
              height={160}
              style={{
                imageRendering: 'pixelated',
                border: '1px solid var(--border)',
                borderRadius: 8
              }}
            />
            <p className="muted">{file?.name} · 8×8 pixels</p>
          </div>
        )}

        <button className="primary" onClick={predict} disabled={!file || busy}>
          {busy ? <LoaderCircle size={16} className="spin" /> : <Upload size={16} />}
          {busy ? 'Analyzing image...' : 'Predict image'}
        </button>
      </section>

      {error && <div className="error-box">{error}</div>}

      {result && (
        <section className="panel">
          <div className="panel-head">
            <h3>Classification result</h3>
          </div>

          <div className="notice">
            {result.prediction === 'Benign'
              ? <ShieldCheck size={22} />
              : <AlertTriangle size={22} />}
            <span>
              <b>Prediction: {result.prediction}</b>
              <br />
              Model: {result.model}
              <br />
              Input size: {result.image_size}
            </span>
          </div>

          <h3>Model output scores</h3>
          {Object.entries(result.probabilities).map(([label, score]) => (
            <div key={label} style={{ margin: '16px 0' }}>
              <div className="setting-row">
                <span>{label}</span>
                <b>{Number(score).toFixed(2)}%</b>
              </div>
              <div
                style={{
                  height: 8,
                  background: 'var(--border)',
                  borderRadius: 8,
                  overflow: 'hidden'
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${Math.max(0, Math.min(100, Number(score)))}%`,
                    background: label === 'Attack' ? '#d97757' : '#2a9d78'
                  }}
                />
              </div>
            </div>
          ))}

          <p className="muted">
            Top-class confidence: {result.confidence.toFixed(2)}%.
          </p>
          <p className="muted">{result.note}</p>
        </section>
      )}
    </div>
  );
}
