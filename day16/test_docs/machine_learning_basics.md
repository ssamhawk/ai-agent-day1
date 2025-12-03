# Machine Learning Basics

## What is Machine Learning?

Machine Learning (ML) is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed. It uses statistical techniques to give computers the ability to "learn" patterns from data.

## Types of Machine Learning

### Supervised Learning
The algorithm learns from labeled training data. Common applications:
- **Classification**: Categorizing data (spam detection, image recognition)
- **Regression**: Predicting continuous values (house prices, stock prices)

Example algorithms:
- Linear Regression
- Logistic Regression
- Decision Trees
- Random Forest
- Support Vector Machines (SVM)
- Neural Networks

### Unsupervised Learning
The algorithm finds patterns in unlabeled data:
- **Clustering**: Grouping similar data points (customer segmentation)
- **Dimensionality Reduction**: Reducing the number of features (PCA)

Example algorithms:
- K-Means
- DBSCAN
- Hierarchical Clustering
- Principal Component Analysis (PCA)

### Reinforcement Learning
The algorithm learns by interacting with an environment and receiving rewards or penalties:
- Game playing (AlphaGo)
- Robotics
- Autonomous vehicles

## Key ML Concepts

### Training and Testing
Data is typically split into:
- Training set (70-80%): Used to train the model
- Test set (20-30%): Used to evaluate model performance

### Overfitting and Underfitting
- **Overfitting**: Model performs well on training data but poorly on new data
- **Underfitting**: Model is too simple to capture patterns in data

### Cross-Validation
Technique to assess model performance by splitting data into multiple folds and training/testing on different combinations.

## Common Python Libraries

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

# Load data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Train model
model = LinearRegression()
model.fit(X_train, y_train)

# Make predictions
predictions = model.predict(X_test)

# Evaluate
mse = mean_squared_error(y_test, predictions)
```

## Feature Engineering

The process of creating new features or transforming existing ones to improve model performance:
- Handling missing values
- Encoding categorical variables
- Scaling numerical features
- Creating interaction features
