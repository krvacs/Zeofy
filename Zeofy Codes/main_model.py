import joblib
import numpy as np
from pathlib import Path
import time
from model_selector import ModelSelector

# --- ADD THESE FOR PYINSTALLER ---
# PyInstaller needs to see these explicitly to package them into the .exe
import sklearn
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
try:
    import xgboost
except ImportError:
    pass
# ---------------------------------

# ── PyTorch (optional — only imported when a .pth model is active) ──────────
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("WARNING: PyTorch not installed. ZFY neural-network model will not work.")

class ZFYNeuralNet(nn.Module):
    def __init__(self, input_size: int, num_classes: int):
        super().__init__()
        self.network = nn.Sequential(
            # Hidden Layer 1 (32)
            nn.Linear(input_size, 32),
            nn.BatchNorm1d(32),
            nn.Tanh(),

            # Hidden Layer 2 (64)
            nn.Linear(32, 64),
            nn.BatchNorm1d(64),
            nn.Tanh(),

            # Hidden Layer 3 (16)
            nn.Linear(64, 16),
            nn.BatchNorm1d(16),
            nn.Tanh(),

            # Output Layer
            nn.Linear(16, num_classes),
        )

    def forward(self, x):
        return self.network(x)


# ============================================================
# Helper — build the 12-feature vector (shared by all paths)
# ============================================================
def _build_feature_vector(params: dict):
    sival  = float(params.get("sival",  0.0))
    alval  = float(params.get("alval",  0.0))
    naval  = float(params.get("naval",  0.0))
    mag    = float(params.get("mag",    0.0))
    h20    = float(params.get("h20",    0.0))
    ohval  = float(params.get("ohval",  0.0))
    time_v = float(params.get("time",   0.0))
    temper = float(params.get("temper", 0.0))

    mol_total = sival + alval + naval + mag + h20 + ohval
    if mol_total == 0:
        return None, "molar sum is zero — cannot predict"

    sival_n = sival / mol_total
    alval_n = alval / mol_total
    naval_n = naval / mol_total
    mag_n   = mag   / mol_total
    h20_n   = h20   / mol_total
    ohval_n = ohval / mol_total

    # Ratios computed from normalized values — log1p transformed to match datasetcheck2.py
    si_al_ratio = np.log1p(sival_n / (alval_n + 1e-6))
    oh_si_ratio = np.log1p(ohval_n / (sival_n + 1e-6))
    na_al_ratio = np.log1p(naval_n / (alval_n + 1e-6))
    oh_al_ratio = np.log1p(ohval_n / (alval_n + 1e-6))

    X = np.array([[
        sival_n, alval_n, naval_n, h20_n, mag_n, ohval_n,
        time_v, temper,
        si_al_ratio, oh_si_ratio, na_al_ratio, oh_al_ratio
    ]], dtype=np.float32)

    return X, None


# ============================================================
# Helper — load one version's files independently
# ============================================================
def _load_version_artifacts(version_key: str):
    """Load scaler, encoder, and model for a specific version key.
    Returns (sklearn_model_or_nn, scaler, label_encoder, is_pytorch) or raises."""
    config    = ModelSelector.MODEL_CONFIGS[version_key]
    from model_selector import get_resource_path
    base_path = get_resource_path(config["model_path"])

    model_file   = base_path / config["model_file"]
    scaler_file  = base_path / config["scaler_file"]
    encoder_file = base_path / config["encoder_file"]

    for label, path in [("Model", model_file), ("Scaler", scaler_file), ("Encoder", encoder_file)]:
        if not path.exists():
            raise FileNotFoundError(f"{label} file not found: {path}")

    scaler        = joblib.load(scaler_file)
    label_encoder = joblib.load(encoder_file)
    is_pytorch    = config["model_file"].endswith(".pth")

    if is_pytorch:
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch not installed — cannot load ZFY model.")
        num_classes = len(label_encoder.classes_)
        # Fixed architecture matching datasetcheck.py — no best_params.pkl needed
        nn_model = ZFYNeuralNet(input_size=12, num_classes=num_classes)
        state    = torch.load(model_file, map_location="cpu", weights_only=True)
        if isinstance(state, dict) and "model_state_dict" in state:
            state = state["model_state_dict"]
        nn_model.load_state_dict(state)
        nn_model.eval()
        model = nn_model
    else:
        model = joblib.load(model_file)

    return model, scaler, label_encoder, is_pytorch


def _infer(model, scaler, label_encoder, is_pytorch, X, n=5):
    """Run scaled inference and return top-n result dict."""
    X_scaled = scaler.transform(X)
    if is_pytorch:
        tensor = torch.tensor(X_scaled, dtype=torch.float32)
        with torch.no_grad():
            logits = model(tensor)
            probs  = torch.softmax(logits, dim=1).numpy()[0]
    else:
        probs = model.predict_proba(X_scaled)[0]

    top_indices     = np.argsort(probs)[-n:][::-1]
    top_frameworks  = label_encoder.inverse_transform(top_indices)
    top_confidences = probs[top_indices]

    return {
        "success": True,
        "predicted_framework": top_frameworks[0],
        "confidence": float(top_confidences[0] * 100),
        "top_predictions": [
            {"framework": fw, "probability": float(conf * 100)}
            for fw, conf in zip(top_frameworks, top_confidences)
        ]
    }


# ============================================================
# Main model class
# ============================================================
class ZeoliteModel:

    def __init__(self):
        self.model         = None
        self.scaler        = None
        self.label_encoder = None
        self.model_loaded  = False
        self._loaded_version = None
        self._is_pytorch   = False

    # --------------------------------------------------
    # LOAD MODEL FILES  (sklearn OR PyTorch)
    # --------------------------------------------------
    def _load_model_files(self):
        try:
            version       = ModelSelector.get_current_version()
            display_label = ModelSelector.get_display_label()
            model_name    = ModelSelector.get_model_name()
            is_pytorch    = ModelSelector.is_pytorch_model()

            print("\n" + "=" * 60)
            print("  LOADING MODEL FILES")
            print(f"  Version  : {version}  |  Backend: {'PyTorch' if is_pytorch else 'sklearn'}")
            print("=" * 60)

            model, scaler, label_encoder, is_pytorch = _load_version_artifacts(version)

            self.model         = model
            self.scaler        = scaler
            self.label_encoder = label_encoder
            self._is_pytorch   = is_pytorch
            self.model_loaded  = True
            self._loaded_version = version

            print(f"  ✓ Loaded: {display_label} ({model_name})")
            print(f"  ✓ Frameworks: {list(label_encoder.classes_)}")
            print("=" * 60 + "\n")

        except Exception as e:
            self.model_loaded    = False
            self._loaded_version = None
            self._is_pytorch     = False
            print(f"\n✗ ERROR loading model files: {e}\n")
            raise

    def _ensure_model(self):
        active = ModelSelector.get_current_version()
        if active != self._loaded_version:
            print(f"[ZeoliteModel] Switching model: '{self._loaded_version}' → '{active}'")
            try:
                self._load_model_files()
            except Exception as e:
                print(f"[ZeoliteModel] Failed to load model for version '{active}': {e}")
                return False
        return True

    def _run_inference(self, X_scaled: np.ndarray) -> np.ndarray:
        if self._is_pytorch:
            tensor = torch.tensor(X_scaled, dtype=torch.float32)
            with torch.no_grad():
                logits = self.model(tensor)
                probs  = torch.softmax(logits, dim=1).numpy()[0]
        else:
            probs = self.model.predict_proba(X_scaled)[0]
        return probs

    # --------------------------------------------------
    # PREDICT DIRECTLY FROM DICT
    # --------------------------------------------------
    def predict_from_dict(self, params, n=5, progress_callback=None):
        if not self._ensure_model() or not self.model_loaded:
            print("ERROR: Model not loaded")
            return None
        try:
            if progress_callback: progress_callback(10)
            X, err = _build_feature_vector(params)
            if err:
                print(f"ERROR: {err}")
                return None
            if progress_callback: progress_callback(30)
            time.sleep(0.05)
            X_scaled = self.scaler.transform(X)
            if progress_callback: progress_callback(50)
            time.sleep(0.05)
            probs = self._run_inference(X_scaled)
            if progress_callback: progress_callback(70)
            time.sleep(0.05)
            top_indices     = np.argsort(probs)[-n:][::-1]
            top_frameworks  = self.label_encoder.inverse_transform(top_indices)
            top_confidences = probs[top_indices]
            if progress_callback: progress_callback(90)
            time.sleep(0.05)
            results = {
                "success": True,
                "predicted_framework": top_frameworks[0],
                "confidence": float(top_confidences[0] * 100),
                "top_predictions": [
                    {"framework": fw, "probability": float(conf * 100)}
                    for fw, conf in zip(top_frameworks, top_confidences)
                ]
            }
            if progress_callback: progress_callback(100)
            return results
        except Exception as e:
            print(f"ERROR during prediction: {e}")
            import traceback; traceback.print_exc()
            return None

    def predict_all_models(self, params, n=5, progress_callback=None):
        all_versions = list(ModelSelector.MODEL_CONFIGS.keys())
        results      = {}
        errors       = {}
        n_models     = len(all_versions)

        X, err = _build_feature_vector(params)
        if err:
            print(f"ERROR building feature vector: {err}")
            return None

        for i, version_key in enumerate(all_versions):
            label = ModelSelector.MODEL_CONFIGS[version_key].get("display_label", version_key)
            print(f"\n[predict_all_models] ({i+1}/{n_models}) Loading {label} ...")
            try:
                model, scaler, label_encoder, is_pytorch = _load_version_artifacts(version_key)
                result = _infer(model, scaler, label_encoder, is_pytorch, X, n=n)
                results[version_key] = result
                print(f"  ✓ {label}: {result['predicted_framework']} @ {result['confidence']:.1f}%")
            except Exception as e:
                print(f"  ✗ {label} failed: {e}")
                errors[version_key] = str(e)
                results[version_key] = None

            if progress_callback:
                progress_callback(int((i + 1) / n_models * 100))

        results["errors"] = errors
        return results

    # --------------------------------------------------
    # TOP-N PREDICTION WITH PROGRESS
    # --------------------------------------------------
    def predict_top_n(self, params, n=5, progress_callback=None):
        if not self._ensure_model() or not self.model_loaded:
            print("Model not loaded!")
            return None
        if progress_callback: progress_callback(40)
        X, err = _build_feature_vector(params)
        if err:
            print(f"ERROR: {err}")
            return None
        if progress_callback: progress_callback(50)
        time.sleep(0.1)
        X_scaled = self.scaler.transform(X)
        if progress_callback: progress_callback(60)
        time.sleep(0.1)
        probs = self._run_inference(X_scaled)
        if progress_callback: progress_callback(80)
        time.sleep(0.1)
        top_indices     = np.argsort(probs)[-n:][::-1]
        top_frameworks  = self.label_encoder.inverse_transform(top_indices)
        top_confidences = probs[top_indices]
        if progress_callback: progress_callback(90)
        time.sleep(0.1)
        return list(zip(top_frameworks, top_confidences))

    # --------------------------------------------------
    # FULL PIPELINE
    # --------------------------------------------------
    def process_full_pipeline(self, filename="zeolite_parameters.txt", n=5, progress_callback=None):
        if not self._ensure_model() or not self.model_loaded:
            print("ERROR: Model not loaded")
            return None
        params = self.preprocess_from_file(filename, progress_callback)
        if params is None:
            return None
        topN = self.predict_top_n(params, n=n, progress_callback=progress_callback)
        if not topN:
            return None
        if progress_callback: progress_callback(100)
        return {
            "success": True,
            "predicted_framework": topN[0][0],
            "confidence": topN[0][1] * 100,
            "top_predictions": [
                {"framework": fw, "probability": conf * 100}
                for fw, conf in topN
            ]
        }

    def preprocess_from_file(self, filename="zeolite_parameters.txt", progress_callback=None):
        if progress_callback: progress_callback(10)
        param_data = {}
        try:
            with open(filename, "r") as f:
                lines = f.readlines()
            if progress_callback: progress_callback(20)
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    try:
                        param_data[key.strip()] = float(value.strip())
                    except ValueError:
                        param_data[key.strip()] = 0.0
            if progress_callback: progress_callback(30)
            required_keys = ["sival","alval","naval","mag","h20","ohval","time","temper"]
            for k in required_keys:
                if k not in param_data:
                    param_data[k] = 0.0
            if progress_callback: progress_callback(40)
            return param_data
        except FileNotFoundError:
            print(f"\nERROR: File not found → {filename}")
            return None
        except Exception as e:
            print(f"\nERROR reading file: {e}")
            return None

    def preprocess_from_dict(self, param_dict):
        required_keys = ["sival","alval","naval","mag","h20","ohval","time","temper"]
        return {k: float(param_dict.get(k, 0.0)) for k in required_keys}


if __name__ == "__main__":
    pass