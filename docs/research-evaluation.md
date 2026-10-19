# Research Evaluation Method

## Data

The built-in experiment uses reproducible synthetic normal and abnormal samples generated with NumPy. Features are packet rate, response time, CPU and memory percentages, failed requests, connection frequency, bytes sent, session duration, reconnections, and error frequency. These are generic synthetic telemetry features; no patient measurements are generated.

## Model

An Isolation Forest is trained on generated normal samples. A separate held-out test set includes unseen normal samples and separately generated abnormal samples. The seed is fixed by default for reproducibility. A sample's `decision_function` output is a model score, not a calibrated probability.

## Metrics

- TP: anomalous samples predicted anomalous.
- TN: normal samples predicted normal.
- FP: normal samples predicted anomalous.
- FN: anomalous samples predicted normal.
- Precision = TP / (TP + FP), or zero when denominator is zero.
- Recall / detection rate = TP / (TP + FN), or zero when denominator is zero.
- F1 = 2 × precision × recall / (precision + recall), or zero if both are zero.
- False-positive rate = FP / (FP + TN), or zero when denominator is zero.
- False-negative rate = FN / (FN + TP), or zero when denominator is zero.

## Interpretation

Results are measurements of a generated distribution and implementation, not evidence of performance against real-world IoT attacks. Real evaluation would require representative data, documented labeling, an appropriate split strategy, multiple seeds, measured runtime and resource overhead, baselines, and a reproducible protocol.

## Limitations

Synthetic distributions are simplified and may be easier to separate than real behavior. Communication and credential detections are rule-based. Risk weights and severity-to-layer scores are initial prototype assumptions. No superiority claim should be made without a comparative experiment.
