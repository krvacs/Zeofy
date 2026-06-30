# Zeolite Framework Yield Predictor (ZFY) Model Training Pipeline
This repository contains the backend machine learning training pipeline for the ZFY PyTorch Neural Network model. The script is designed to perform extensive hyperparameter tuning, train a deep learning classifier to predict zeolite framework codes from chemical compositions, and automatically generate detailed evaluation artifacts.

# Core Features
1. Automated Hyperparameter Optimization: Implements a robust Random Search over a wide configuration space across up to 463 trials.
2. Rigorous Validation: Uses 10-Fold Stratified Cross-Validation to ensure model generalization and reliability.
3. Artifact Generation: Automatically generates and saves model artifacts for the best configuration, including PyTorch .pth weights, .pkl scalers/encoders, learning curves, confusion matrices, and permutation feature importance charts.
4. Comprehensive Logging: Records all trial hyperparameters, training metrics, cross-validation means/standard deviations, and test metrics into a heavily formatted Excel workbook (best_model_results.xlsx).
5. Interactive CLI & Bulk Processing: Includes a command-line interface for real-time single-sample predictions (displaying top-3 candidates) and a bulk prediction function to process entire Excel datasets.

# Methodology & Feature Engineering
The neural network (ZFY) expects a 12-feature input vector. This includes 8 base chemical and synthesis parameters, plus 4 engineered log-transformed ratios designed to capture non-linear chemical relationships. Base Features:
1. Silica (sival)
2. Alumina (alval)
3. Sodium (naval)
4. Water (h20)
5. Extra Framework Cation (mag)
6. Hydroxide (ohval)
7. Time
8. Temperature (temper)

Engineered Log-Ratios:
To prevent division-by-zero errors and scale large variance, the pipeline calculates:
1. epsilon = 1e-6
2. si_al_ratio = np.log1p(sival / (alval + epsilon))
3. oh_si_ratio = np.log1p(ohval / (sival + epsilon))
4. na_al_ratio = np.log1p(naval / (alval + epsilon))
5. oh_al_ratio = np.log1p(ohval / (alval + epsilon))

# Requirements & Dependencies
To execute the training script, the following Python libraries are required:
1. torch (PyTorch - CUDA supported for GPU acceleration)
2. scikit-learn (for validation splits, metrics, scaling, and a custom PyTorch estimator wrapper)
3. pandas & numpy (for data manipulation)
4. matplotlib (for generating visual artifacts)
5. openpyxl (for styled Excel logging)
6. joblib (for exporting the scaler and label encoder)

# Usage Guide
1. Model Training and Random Search: Run the script directly to initiate the training sequence. The script will loop through the defined Random Search space, evaluate via Stratified K-Fold, and dynamically create a saved_model/Config_XXX/ directory containing all artifacts for the highest-performing architecture.
2. Interactive CLI Predictor: Upon completing the search (or if you bypass the training loop and load a saved model), the script launches an interactive terminal prompt.
Input your raw chemical values when prompted.
It will output the predicted Zeolite Phase along with a confidence percentage for the top 3 candidates.
The script will automatically apply the exact log-transformations and standard scaling used during training.
3. Bulk Excel Prediction: You can uncomment and utilize the bulk_predict_excel(file_path) function to pass a .xlsx file. The function will:
   Recreate the exact feature engineering.
   Scale the data precisely like the training set.
   Append Predicted Framework and Confidence Score columns to the data.
   Export a new file labeled _predictions.xlsx.

# Notes on Hyperparameter Logging & Compatibility

Since the Random Search algorithm samples from a flattened, static hyperparameter dictionary (`HYPERPARAMETER_SPACE`), it occasionally selects combinations where certain parameters are contextually inactive. 

# Expected Logging Behavior
While the script includes logic to gracefully ignore incompatible parameters during execution (ensuring the model trains without crashing), the Excel logger blindly records the entire sampled configuration. As a result, the `best_model_results.xlsx` file will contain columns for hyperparameters that were not actually utilized in that specific trial. 

*Example:* If a trial selects `lr_scheduler: cosine`, the script might still sample and log a value for `plateau_patience` or `step_size`. 

# Recommended Post-Processing
To maintain a clean and analyzable dataset, it is highly recommended to perform a post-processing cleanup on the Excel output. You can utilize LLM tools (like Claude AI or ChatGPT) or write a quick Python script to parse the Excel file and automatically drop or nullify columns containing mutually exclusive or incompatible hyperparameters based on the active configuration rules.
