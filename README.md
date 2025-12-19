# PATHS
AI-Powered Decision System

PATHS: The Coordinate Engine – ML Module
Overview
PATHS is a machine learning–powered decision engine designed to predict student risk categories and recommend actions such as ADVANCE, HOLD, or RETREAT based on academic and behavioral indicators. This README describes only the ML and API layer you have implemented, covering the synthetic data generation, model training, decision logic, and FastAPI service interface.

The system takes structured student data (attendance, internal marks, assignments, study hours, backlog count, stress level), predicts a risk level, and then applies rule-based overrides to generate an interpretable action and explanation.

Project Structure
At a high level, the project is organized into the following directories and responsibilities:

data/

raw/

Holds the synthetic dataset (student_data.csv) and the data generation script.

processed/

Reserved for any processed or transformed datasets that may be produced later.

model/

Contains the training script, prediction helper, and model package initialization.

Stores the trained model artifact (paths_model.pkl) and the scaler (scaler.pkl).

engine/

Encapsulates business and decision logic:

Mapping the model’s numeric prediction to semantic labels.

Applying rule-based overrides and confidence thresholds.

api/

FastAPI application and routes that expose the decision engine as an HTTP API.

utils/

Utility components such as data preprocessing and metrics helpers.

venv/

Local virtual environment for isolating Python dependencies (not committed in most setups).

This structure cleanly separates concerns: data, modeling, decision logic, and API, making the ML component easier to extend and integrate with a larger system.

Core Workflow
The ML pipeline follows a clear sequence from data generation to serving predictions:

Environment and Dependencies

A Python virtual environment is created and activated.

Core dependencies include:

Numerical and data handling libraries (NumPy, pandas).

Machine learning framework (scikit-learn).

Visualization (matplotlib, if needed later).

Web service stack (FastAPI and Uvicorn).

Synthetic Data Generation

A script in data/raw/ generates a synthetic dataset of student records.

Each record includes:

Attendance percentage.

Internal assessment marks.

Assignment performance.

Daily study hours.

Backlog (arrear) count.

Self-reported or inferred stress level.

A target label risk_level indicating:

0 – ADVANCE

1 – HOLD

2 – RETREAT

Data is generated for three archetypal profiles:

Advance: high attendance, higher internal marks, strong assignments, more study hours, low backlogs, low stress, low risk.

Hold: moderate performance and risk, with middling attendance, marks, backlogs, and stress.

Retreat: low performance, higher backlog counts and stress, representing high-risk students.

Class distribution is controlled via fixed proportions for advance, hold, and retreat categories.

A small amount of label noise is intentionally introduced by randomly flipping a fraction of risk_level values to mimic real-world imperfections.

The final dataset is shuffled and saved as data/raw/student_data.csv.

Preprocessing and Data Splitting

A preprocessing utility in utils/:

Loads the raw CSV dataset.

Splits features (X) and target labels (y) by separating out the risk_level column.

Performs a stratified train–test split to preserve the class distribution in both subsets.

Fits a StandardScaler only on the training data to avoid data leakage.

Applies the trained scaler to both training and test feature sets.

Persists the scaler to disk (model/scaler.pkl) for consistent use at inference time.

The function returns scaled training and test sets along with their corresponding labels.

Model Training and Evaluation

The training script in model/:

Calls the preprocessing utility to obtain scaled X_train, X_test, y_train, and y_test.

Instantiates a RandomForestClassifier configured for multi-class classification with:

A specified number of trees.

Custom class weights to handle class imbalance among the three risk levels.

Depth constraints and a fixed random seed for reproducibility.

Fits the model on the training data.

Evaluates the model on the test set, reporting:

Overall accuracy.

A detailed classification report (precision, recall, F1-score per class).

Saves the trained model (model/paths_model.pkl) for use during prediction.

Prediction Helper

A predictor module in model/ is responsible for:

Loading the trained model and the saved scaler once at import.

Exposing a predict function that:

Accepts raw numerical inputs in a fixed order:

Attendance, internal marks, assignments, study hours, backlog count, stress level.

Converts the input to a NumPy array and reshapes it.

Scales the input using the same StandardScaler used during training.

Obtains class probabilities from the model’s predict_proba.

Determines the predicted class by taking the highest probability.

Extracts the associated confidence value for that prediction.

Returns both the discrete prediction and the model’s confidence score.

The module includes a simple runnable example to manually test prediction from the command line.

Decision Logic Layer

The decision engine in engine/ translates model outputs into human-meaningful actions:

A label map converts numeric risk_level values to string labels:

0 → ADVANCE

1 → HOLD

2 → RETREAT

A resolver function:

Accepts the model’s prediction, confidence, and the original raw input features.

Applies rule-based overrides before trusting the model:

If attendance is very low or a combination of high backlogs and high stress is detected, the system forces a RETREAT decision with a “critical risk” reason, regardless of the model output.

Checks confidence:

If the model’s confidence is below a threshold (for example, 0.6), it defaults to HOLD with a “low confidence” explanation.

Otherwise, translates the numeric prediction into:

ADVANCE with a message about stable performance.

HOLD with a message about moderate risk and monitoring.

RETREAT with a message about high risk predicted by the model.

A coordinator function:

Orchestrates the full decision:

Calls the predictor to get the model’s prediction and confidence.

Calls the resolver to determine action and reason.

Returns a structured dictionary containing:

The prediction label (ADVANCE/HOLD/RETREAT).

The action (which can be influenced by rules).

The rounded confidence score.

A textual reason for the decision.

FastAPI Service Layer

The web API in api/ turns the decision engine into a REST endpoint:

An application file instantiates a FastAPI app and includes a router.

A routes module:

Defines a Pydantic model representing the expected student input payload with the same fields used during training.

Exposes a POST endpoint (e.g., /coordinate) that:

Receives validated JSON data.

Converts it into the ordered list required by the coordinator.

Calls the decision engine and returns its response object directly.

The service is run via a command like:

Starting Uvicorn with the FastAPI application in reload mode from the project root, enabling local testing and development.

Usage Flow
Putting everything together, a typical usage flow for this ML module is:

Initial Setup

Create the project directory and subfolders.

Initialize a virtual environment and install dependencies using a requirements file.

Ensure initialization files exist to treat key directories as Python packages.

Data Creation

Execute the synthetic data generation script to produce student_data.csv in the raw data directory.

Model Training

Run the training script as a module so it can access the package structure correctly.

Review printed accuracy and classification metrics.

Confirm that both the model and scaler files are written to the model/ directory.

Local Prediction Check

Invoke the predictor script directly to test a sample student profile and see the predicted risk level and confidence.

Decision Engine Test

In an interactive session, import the coordinator function from the decision engine.

Pass in a student profile list and print the returned dictionary.

Verify that:

The prediction field matches the label mapping.

The action and reason reflect both model output and override rules.

API Interaction

Start the FastAPI application with Uvicorn from the project root.

Use a REST client or browser-based tool (such as the automatically generated /docs Swagger UI) to:

Submit POST requests to the coordinate endpoint with JSON student data.

Inspect the structured JSON response containing prediction, action, confidence, and justification.
