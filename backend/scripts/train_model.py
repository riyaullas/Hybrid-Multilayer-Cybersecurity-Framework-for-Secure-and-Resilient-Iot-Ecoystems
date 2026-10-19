import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.ml_service import evaluate, train_model
out=Path(__file__).resolve().parents[2]/'data'/'generated'; out.mkdir(parents=True,exist_ok=True)
result=evaluate(); (out/'synthetic_evaluation.json').write_text(json.dumps(result,indent=2))
import joblib
joblib.dump(train_model(), out/'isolation_forest.joblib')
print('Saved model:', out/'isolation_forest.joblib')
print(json.dumps(result,indent=2))
