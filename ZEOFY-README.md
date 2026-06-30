# Zeofy Application

Zeofy is an intelligent, high-performance desktop application built using CustomTkinter designed to optimize and predict zeolite frameworks based on chemical compositions and synthesis parameters. The platform bridges machine learning workflows with materials science engineering, offering both single-sample synthesis simulations and high-throughput batch execution.

# Core Features
1. Multi-Model Inference Architecture: Leverages a custom PyTorch Multi-Layer Perceptron neural network model (ZFY) alongside five traditional scikit-learn machine learning classifiers (ZLF Family: XGBoost, Random Forest, Extra Trees, Support Vector Machines, and Decision Trees).
2. Interactive Synthesis Dashboard (Synthesize): Allows fine-grained engineering adjustments for 9 structural features (Silicon, Aluminum, Sodium, Water Content, Extra-Framework cations, Hydroxyl concentration, Synthesis Time, Temperature, and Metakaolin).
3. Real-time Material Calculations: Dynamic programmatic derivation of raw ingredient mass configurations in grams matching precise target compositions.
4. Bulk Processing & Batch Analytics (Bulk Import): Validates and handles parallel multi-row evaluation over spreadsheets (.xlsx/.xls), caching full cross-model assessments with dynamic error boundaries and automated format alert highlight rendering.
5. Responsive Visualizations: Animated interactive graphical systems charting categorical probability arrays (FAU, LTA, CHA, MOR, MFI) alongside real-time radial gauges showcasing framework classification certainty.
6. Integrated Feedback Matrix (Review): QR-code generator linking to active cloud appraisal forms to streamline user-experience collection.

# Repository Architecture
├── app.py                # Core application loop & centralized preloading lifecycle
├── sidebar.py            # Responsive drawer navigating views & managing model variations
├── main.py               # Single observation synthesis suite (MainPanel)
├── main_feature.py       # Custom tween-engine charts & parameter entry layouts
├── main_model.py         # Standardized 12-feature processing pipeline & model inference core
├── bulk.py               # Batch-analytics framework (BulkPanel)
├── bulk_feature.py       # Sheet validation layers & distribution chart components
├── bulk_model.py         # Multi-model batch compute framework & styled spreadsheet exporter
├── model_selector.py     # Global configuration dictionary, asset lookups, & state coordinator
├── review.py             # Integrated feedback module & dynamic vector QR generator
├── deployedModels/       # [EXCLUDED] Directory for Pickled matrices, scalers, and .pth files
└── icons/                # User interface graphics, loading sequences, and alert indicators

# System Prerequisites
The core package relies on explicit numerical math, scientific optimization, and interface rendering libraries:
1. GUI Engine: customtkinter, pillow
2. Data Processing: numpy, pandas, openpyxl
3. Mathematical Backends: scikit-learn, xgboost, torch (optional, required for the ZFY engine)
4. Analytical Features: matplotlib, qrcode

# Installation and Setup
1. Ensure a proper modern Python instance is operational (3.9, Python3.11 recommended). Clone the repository and configure an isolated virtual environment:
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
2. Install all required modules via package manager:
   pip install customtkinter pillow numpy pandas openpyxl scikit-learn xgboost torch matplotlib qrcode
3. Launching the App
   python app.py

# Zeolite Framework Yield Predictor (ZFY Model)
