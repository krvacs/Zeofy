from pathlib import Path
import sys
import os


def get_resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Normal Python execution - use current directory
        base_path = os.path.abspath(".")
    
    return Path(base_path) / relative_path


class ModelSelector:
    
    _instance = None
    _current_version = "ZLF_XGBoost"  # Default version
    
    # Model configuration mapping
    MODEL_CONFIGS = {
        # ── ZFY ──────────────────────────────────────────────────────────────
        "ZFY": {
            "name": "Neural Network",
            "display_label": "ZFY",
            "model_path": "deployedModels/ZFY",
            "model_file": "neural_network_model.pth",
            "scaler_file": "scaler.pkl",
            "encoder_file": "label_encoder.pkl",
            "description": "Neural Network model for ZFY zeolite framework prediction",
        },
        # ── ZLF sub-models ───────────────────────────────────────────────────
        "ZLF_ExtraTrees": {
            "name": "Extra Trees Classifier",
            "display_label": "ZLF · Extra Trees",
            "model_path": "deployedModels/Extra Trees Model Result",
            "model_file": "extra_trees_model.pkl",
            "scaler_file": "scaler.pkl",
            "encoder_file": "label_encoder.pkl",
            "description": "Extra Trees Classifier for ZLF zeolite framework prediction",
        },
        "ZLF_XGBoost": {
            "name": "XGBoost",
            "display_label": "ZLF · XGBoost",
            "model_path": "deployedModels/Extreme Gradient Boosting",
            "model_file": "xgboost_model.pkl",
            "scaler_file": "scaler.pkl",
            "encoder_file": "label_encoder.pkl",
            "description": "XGBoost model for ZLF zeolite framework prediction",
        },
        "ZLF_RandomForest": {
            "name": "Random Forest",
            "display_label": "ZLF · Random Forest Result",
            "model_path": "deployedModels/Random Forest Result",
            "model_file": "random_forest_model.pkl",
            "scaler_file": "scaler.pkl",
            "encoder_file": "label_encoder.pkl",
            "description": "Random Forest model for ZLF zeolite framework prediction",
        },
        "ZLF_SVM": {
            "name": "SVM",
            "display_label": "ZLF · SVM",
            "model_path": "deployedModels/SVM",
            "model_file": "svm_model.pkl",
            "scaler_file": "scaler.pkl",
            "encoder_file": "label_encoder.pkl",
            "description": "Support Vector Machine for ZLF zeolite framework prediction",
        },
        "ZLF_DecisionTree": {
            "name": "Decision Tree",
            "display_label": "ZLF · Decision Tree",
            "model_path": "deployedModels/Decision Tree",
            "model_file": "decision_tree_model.pkl",
            "scaler_file": "scaler.pkl",
            "encoder_file": "label_encoder.pkl",
            "description": "Decision Tree model for ZLF zeolite framework prediction",
        },
    }

    # Keys that belong to the ZLF family (used by sidebar to group them)
    ZLF_VERSIONS = ["ZLF_ExtraTrees", "ZLF_XGBoost", "ZLF_RandomForest", "ZLF_SVM", "ZLF_DecisionTree"]
    
    def __new__(cls):
        """Singleton pattern - only one instance exists"""
        if cls._instance is None:
            cls._instance = super(ModelSelector, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize model selector"""
        pass
    
    @classmethod
    def set_version(cls, version):
        """Set the active model version."""
        if version in cls.MODEL_CONFIGS:
            cls._current_version = version
            cfg = cls.MODEL_CONFIGS[version]
            print("\n" + "=" * 60)
            print("  MODEL SWITCHED")
            print("=" * 60)
            print(f"  Version key  : {version}")
            print(f"  Display name : {cfg['display_label']}")
            print(f"  Algorithm    : {cfg['name']}")
            print(f"  Description  : {cfg['description']}")
            print(f"  Model path   : {cfg['model_path']}")
            print("=" * 60 + "\n")
        else:
            print(f"\nWarning: Unknown version '{version}', keeping '{cls._current_version}'\n")
    
    @classmethod
    def get_current_version(cls):
        return cls._current_version
    
    @classmethod
    def get_model_config(cls):
        return cls.MODEL_CONFIGS.get(cls._current_version)
    
    @classmethod
    def get_model_path(cls):
        config = cls.get_model_config()
        return get_resource_path(config["model_path"])
    
    @classmethod
    def get_model_files(cls):
        config = cls.get_model_config()
        base_path = get_resource_path(config["model_path"])
        
        return {
            "model": base_path / config["model_file"],
            "scaler": base_path / config["scaler_file"],
            "encoder": base_path / config["encoder_file"]
        }
    
    @classmethod
    def get_model_name(cls):
        config = cls.get_model_config()
        return config["name"]
    
    @classmethod
    def get_model_description(cls):
        config = cls.get_model_config()
        return config["description"]
    
    @classmethod
    def get_display_label(cls):
        config = cls.get_model_config()
        return config.get("display_label", cls._current_version)

    @classmethod
    def is_zlf_version(cls):
        return cls._current_version in cls.ZLF_VERSIONS

    @classmethod
    def is_pytorch_model(cls):
        config = cls.get_model_config()
        return config.get("model_file", "").endswith(".pth")

    @classmethod
    def print_current_config(cls):
        config = cls.get_model_config()
        files = cls.get_model_files()
        
        print("\n" + "="*60)
        print("CURRENT MODEL CONFIGURATION")
        print("="*60)
        print(f"Version: {cls._current_version}")
        print(f"Display: {config['display_label']}")
        print(f"Model Type: {config['name']}")
        print(f"Description: {config['description']}")
        print(f"\nModel Files:")
        print(f"  Model:   {files['model']}")
        print(f"  Scaler:  {files['scaler']}")
        print(f"  Encoder: {files['encoder']}")
        
        # Check if files exist
        print(f"\nFile Status:")
        for name, path in files.items():
            exists = "✓ EXISTS" if path.exists() else "✗ NOT FOUND"
            print(f"  {name}: {exists}")
        
        print("="*60 + "\n")


# Convenience function for easy import
def get_model_selector():
    return ModelSelector()


# Test function
def test_model_selector():
    selector = ModelSelector()
    
    print("Testing default version (ZFY):")
    selector.print_current_config()
    
    print("\nSwitching to ZLF_ExtraTrees:")
    selector.set_version("ZLF_ExtraTrees")
    selector.print_current_config()

    print("\nSwitching to ZLF_RandomForest:")
    selector.set_version("ZLF_RandomForest")
    selector.print_current_config()
    
    print("\nSwitching back to ZFY:")
    selector.set_version("ZFY")
    selector.print_current_config()
    
    print("\nTesting invalid version:")
    selector.set_version("INVALID")
    selector.print_current_config()


if __name__ == "__main__":
    test_model_selector()