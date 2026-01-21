# Customer Churn Prediction - MLOps Project

A comprehensive machine learning operations (MLOps) project that predicts customer churn using a Random Forest classifier. The project includes data generation, model training, and a FastAPI-based inference server for real-time predictions.

## Table of Contents
- [Overview](#overview)
- [Project Structure](#project-structure)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [1. Generate Synthetic Data](#1-generate-synthetic-data)
  - [2. Train the Model](#2-train-the-model)
  - [3. Run the API Server](#3-run-the-api-server)
- [API Documentation](#api-documentation)
- [Model Information](#model-information)
- [Testing](#testing)
- [Technologies Used](#technologies-used)
- [License](#license)

## Overview

This MLOps project demonstrates a complete machine learning workflow for predicting customer churn. The system uses historical customer data including age, tenure, charges, and support interactions to predict the likelihood of a customer leaving the service.

**Key Highlights:**
- Synthetic data generation for reproducible experiments
- Random Forest classification model with performance metrics
- RESTful API for real-time predictions
- Interactive FastAPI documentation (Swagger UI)
- Production-ready code structure

## Project Structure

```
MLOPs-Project/
├── api.py                  # FastAPI inference server
├── train.py                # Model training script
├── generate_data.py        # Synthetic data generation
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── LICENSE                 # License file
├── data/
│   └── churn_data.csv     # Generated customer data
└── models/
    └── churn_model.pkl    # Trained model (created after training)
```

## Features

- **Data Generation**: Create synthetic customer data with realistic churn patterns
- **Model Training**: Train a Random Forest classifier with evaluation metrics
- **RESTful API**: FastAPI server with automatic documentation
- **Health Check**: Monitor API availability
- **Probability Predictions**: Get both binary predictions and churn probabilities
- **Interactive UI**: Test predictions using Swagger UI at `/docs`

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

## Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd MLOPs-Project
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### 1. Generate Synthetic Data

Create the training dataset with 1,000 customer records:

```bash
python generate_data.py
```

**Output:**
```
Generated 1000 samples
Churn rate: ~30-40%
```

This creates `data/churn_data.csv` with the following features:
- `customer_id`: Unique identifier
- `age`: Customer age (18-70)
- `tenure_months`: Length of service (1-72 months)
- `monthly_charges`: Monthly billing amount ($20-$120)
- `total_charges`: Cumulative charges ($100-$8,000)
- `num_support_calls`: Support call count (0-10)
- `churn`: Target variable (0 = retained, 1 = churned)

### 2. Train the Model

Train the Random Forest classifier and save it:

```bash
python train.py
```

**Output:**
```
Accuracy: 0.XXXX
AUC-ROC: 0.XXXX
Model saved to models/churn_model.pkl
```

The training script:
- Loads data from `data/churn_data.csv`
- Splits data (80% train, 20% test)
- Trains a Random Forest with 100 estimators
- Evaluates performance using accuracy and AUC-ROC
- Saves the model to `models/churn_model.pkl`

### 3. Run the API Server

Start the FastAPI inference server:

```bash
python api.py
```

**Output:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

The API server will be available at `http://localhost:8000`

## API Documentation

### Interactive Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints

#### Health Check

**GET** `/health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy"
}
```

#### Predict Churn

**POST** `/predict`

Predict customer churn probability.

**Request Body:**
```json
{
  "age": 35,
  "tenure_months": 24,
  "monthly_charges": 75.50,
  "total_charges": 1800.00,
  "num_support_calls": 3
}
```

**Response:**
```json
{
  "churn": 0,
  "churn_probability": 0.23
}
```

- `churn`: Binary prediction (0 = no churn, 1 = churn)
- `churn_probability`: Probability of churn (0.0 to 1.0)

### Example cURL Request

```bash
curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d "{\"age\": 35, \"tenure_months\": 24, \"monthly_charges\": 75.50, \"total_charges\": 1800.00, \"num_support_calls\": 3}"
```

### Example Python Request

```python
import requests

url = "http://localhost:8000/predict"
data = {
    "age": 35,
    "tenure_months": 24,
    "monthly_charges": 75.50,
    "total_charges": 1800.00,
    "num_support_calls": 3
}

response = requests.post(url, json=data)
print(response.json())
```

## Model Information

### Algorithm
**Random Forest Classifier** with 100 estimators

### Features Used
1. `age`: Customer age
2. `tenure_months`: Service duration
3. `monthly_charges`: Monthly billing
4. `total_charges`: Total spending
5. `num_support_calls`: Support interactions

### Evaluation Metrics
- **Accuracy**: Overall prediction correctness
- **AUC-ROC**: Area under the ROC curve (discrimination ability)

### Model Performance
The model is trained on synthetic data with churn patterns based on:
- Higher monthly charges increase churn probability
- More support calls correlate with higher churn
- Shorter tenure increases churn likelihood

## Testing

### Test with FastAPI UI

1. Start the API server: `python api.py`
2. Navigate to http://localhost:8000/docs
3. Expand the `/predict` endpoint
4. Click "Try it out"
5. Enter sample customer data
6. Click "Execute" to see predictions

### Test Cases

**Low Churn Risk Customer:**
```json
{
  "age": 45,
  "tenure_months": 60,
  "monthly_charges": 30.00,
  "total_charges": 1800.00,
  "num_support_calls": 1
}
```

**High Churn Risk Customer:**
```json
{
  "age": 25,
  "tenure_months": 3,
  "monthly_charges": 110.00,
  "total_charges": 330.00,
  "num_support_calls": 8
}
```

## Technologies Used

- **Python 3.8+**: Core programming language
- **pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **scikit-learn**: Machine learning algorithms
- **FastAPI**: Modern web framework for APIs
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation
- **DVC**: Data version control (configured)
- **boto3**: AWS SDK for Python

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Contact

For questions or support, please open an issue in the repository.

---

**Note**: This project uses synthetic data for demonstration purposes. For production use, replace with real customer data and adjust the model accordingly.