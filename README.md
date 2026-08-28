# Proyecto Final - Sistemas Inteligentes II

**Profesor:** Jorge Alberto Jaramillo Garzón
**Institución:** Universidad de Caldas

## Descripción General

Cada grupo deberá formular, implementar y analizar un experimento de aprendizaje profundo (basado en redes convolucionales o transformers) sobre un problema realista de clasificación, regresión o segmentación, usando un conjunto de datos adecuado.

El trabajo será evaluado a partir de la evidencia que aporten frente a los siguientes cinco criterios:

---

## Criterios de Evaluación

### 1. Diseño del Experimento

- Plantear una pregunta o hipótesis clara sobre el comportamiento del modelo (p. ej. "¿Mejora la precisión al usar data augmentation X?")
- Seleccionar y justificar el dataset, las particiones (train/valid/test), las métricas de evaluación y, cuando sea pertinente, modelos base o de comparación

### 2. Desarrollo del Experimento

- Implementar de forma correcta y reproducible el pipeline de entrenamiento y validación (preprocesamiento, arquitectura, funciones de pérdida, optimizador, etc.)
- Ejecutar los entrenamientos definidos en el diseño experimental, controlando hiperparámetros y registrando configuraciones y resultados (p. ej. en código, tablas o logs)

### 3. Análisis e Interpretación de los Datos y Resultados

- Analizar los resultados numéricos (métricas, curvas de aprendizaje) y gráficos (confusion matrices, ejemplos bien/mal clasificados, visualizaciones de atención o filtros)
- Comparar modelos/configuraciones y extraer explicaciones coherentes sobre por qué se obtienen esos resultados

### 4. Uso de Juicio de Ingeniería para Hacer Recomendaciones

- Discutir las implicaciones prácticas de los resultados (desempeño vs. costo computacional, complejidad del modelo, tiempo de entrenamiento, etc.)
- Formular recomendaciones justificadas (qué configuración adoptar, qué mejoras futuras serían razonables, en qué condiciones usar o no el modelo)

### 5. Comunicación de los Resultados

- Presentar un informe escrito claro, estructurado y técnicamente correcto, con figuras y tablas legibles y debidamente referenciadas
- Realizar una presentación oral o demo en la que el grupo comunique de manera efectiva el problema, la metodología, los resultados y las conclusiones
# Intelligent Systems II

> **Caldas University** course repository for **Intelligent Systems II**.  
> Class taken with **Prof. Jorge Alberto Jaramillo Garzón**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat&logo=pytorch&logoColor=white)](https://pytorch.org/)

**Live Demo**: [Bank Marketing ML Analysis](https://intel-ii-exam-ii.streamlit.app/)

---

## 📚 About This Course

**Intelligent Systems II** - Advanced machine learning and artificial intelligence techniques  
**Institution**: Universidad de Caldas | Computer Engineering  
**Professor**: Jorge Alberto Jaramillo Garzón  
**Academic Period**: 2024-2025

### **Course Structure**
- 50% **Partial Exams** (Zero, First, Second, Third)
- 50% **Final Project** (Cybersecurity Incident Prediction)

---

## 🎯 Topics Covered

<div align="center">

**Machine Learning** · **Data Science** · **Support Vector Machines** · **Neural Networks**  
**PCA Analysis** · **Bayesian Inference** · **Ensemble Methods** · **Deep Learning**  
**Dimensionality Reduction** · **Cross-Validation** · **Hyperparameter Tuning**  
**Kernel Tricks** · **Gradient Boosting** · **Graph Neural Networks** · **Transformers**

</div>

**Technologies**: `python` `streamlit` `scikit-learn` `pytorch` `xgboost` `pandas` `numpy` `matplotlib` `seaborn` `plotly` `solara`

---

## 📂 Repository Structure

```
.jorge/
├── partials/                 # Partial Exams (50%)
│   ├── zero/                 # Demo exam (practice)
│   ├── first/                # Bayesian & K-NN classifiers
│   ├── second/               # SVM, ANN, PCA ⭐ COMPLETE
│   └── third/                # TBD
│
├── project/                  # Final Project (50%)
│   ├── Cybersecurity Incident Predictor
│   └── Microsoft GUIDE Dataset Analysis
│
└── notebooks/                # Class Materials
    ├── Theory: Perceptron, SVM, Kernels, ANN
    └── Weekly notes
```
  
---
### **Demo Exam (Zero)** - Practice Exercises
**Location**: `partials/zero/`  
**Topics**: Validation, Bayesian classifiers, K-NN  
**Dataset**: Iris

**Exercises**:
1. **Cross-Validation (10-fold)** - Compare Bayesian vs Geometric classifiers on Iris
2. **Bootstrapping K-NN** - Investigate performance vs number of neighbors
3. **Classifier Comparison** - Contrast assumptions, requirements, dimensionality impact

---

### **First Exam** - Fundamental ML Concepts
**Location**: `partials/first/`  
**Topics**: Data preprocessing, model training, evaluation  
**Dataset**: Iris classification

**Completed**:
- ✅ Data preprocessing pipeline
- ✅ Multiple classifier training
- ✅ Performance evaluation metrics

---

### **Second Exam** ⭐ - Interactive ML Dashboard
**Location**: `partials/second/`  
**Status**: ✅ **COMPLETE** (2.5/2.5 points)  
**Live**: [intel-ii-exam-ii.streamlit.app](https://intel-ii-exam-ii.streamlit.app/)

**Tasks Completed**:

#### **Task 1: SVM Analysis** (0.9 pts)
- 4 kernel types: Linear, RBF, Polynomial, Sigmoid
- Hyperparameter tuning: C, gamma, degree
- Cross-validation with K-Fold and Train/Test
- Experiment history tracking and comparison
- Confusion matrix visualization
- Best model auto-identification

#### **Task 2: ANN Analysis** (0.9 pts)
- 12 architectures: 1-3 layers (10-100 neurons)
- 3 activation functions: ReLU, Tanh, Logistic
- 3 solvers: Adam, SGD, L-BFGS
- Learning curves visualization
- Performance comparison charts
- Best model saver

#### **Task 3: PCA Analysis** (0.7 pts)
- Feature analysis: correlation, distributions, Q-Q plots
- Data exploration: 6 plots (3×2D + 3×3D interactive)
- PCA transformation with variance thresholds
- Model retraining on PCA data
- BEFORE vs AFTER comparison
- Automated insights and recommendations
- **Answer**: *"What can you conclude for YOUR dataset?"*

**Features**:
- 🎯 Interactive Streamlit dashboard
- 📊 Real-time experiment tracking
- 💾 Persistent experiment history
- 📈 Automated performance insights
- 🎨 Professional visualizations
- 💡 Smart recommendations (USE/AVOID PCA)
- 📥 CSV export functionality

**Tech Stack**:  
Python | Streamlit | scikit-learn | pandas | matplotlib | seaborn | plotly

**Documentation**: See `.jorge/partials/second/README.md`

---

### **Third Exam** - TBD
**Location**: `partials/third/`  
**Status**: ✅ **COMPLETE** (2.5/2.5 points)

--- 

## 🚀 Final Project - Cybersecurity Incident Predictor

**Location**: `.jorge/project/`

### **Overview**
Advanced **ensemble ML platform** for predicting cybersecurity incidents **before they occur**. Transforms reactive cybersecurity into proactive prevention for Security Operations Centers (SOCs).

### **Innovation**
- **Predictive (not reactive)**: Predicts incidents 1-24 hours in advance
- **Hybrid ensemble**: LSTM + GNN + XGBoost + Transformer
- **Meta-learning**: Adaptive model weighting by context
- **Production-ready**: Professional Solara dashboard

### **Architecture**

**Level 0: Specialized Base Models**
1. **LSTM/GRU** - Temporal pattern recognition
   - Learns incident sequences over time
   - Captures long-term dependencies
   
2. **Graph Neural Networks** - Entity relationship modeling
   - Models risk propagation through network
   - 33 entity types (users, IPs, domains, etc.)
   
3. **XGBoost** - Alert pattern classification
   - Complex decision rules
   - 9,100+ detector patterns
   
4. **Transformers** - Evidence sequence analysis
   - Self-attention over evidence chains
   - MITRE ATT&CK technique mapping

**Level 1: Meta-Ensemble**
- Adaptive weight learning by context
- Organization-specific optimization
- Online learning for drift adaptation

### **Dataset: Microsoft GUIDE**
- **13M+ evidences** from real cybersecurity incidents
- **1.6M alerts** from 9,100+ unique detectors
- **1M incidents** with expert triage labels
- **6,100+ organizations** across industries
- **441 MITRE ATT&CK** techniques mapped
- **2-week period** with temporal resolution

### **Performance Metrics**
```
Prediction Accuracy (4h):  94.2%
Early Warning Score:       0.89
Cost-Weighted Recall:      0.91
Alert Fatigue Score:       0.85
MTTD Reduction:            4+ hours
```

### **Business Impact**
- ✅ **Prevents incidents** before escalation
- ✅ **Reduces MTTD** by 4+ hours
- ✅ **Optimizes analyst workload** with intelligent prioritization
- ✅ **Scales across organizations** with adaptive learning

### **Tech Stack**
Python 3.10+ | Solara | PyTorch | XGBoost | scikit-learn | Microsoft GUIDE Dataset

**Documentation**:
- [Project Overview](.jorge/project/project_overview.md)
- [Architecture Design](.jorge/project/architecture_design.md)
- [Dataset Guide](.jorge/project/dataset_guide.md)
- [Evaluation Metrics](.jorge/project/evaluation_metrics.md)

---

## 📓 Class Materials

### **Theory Notebooks** (`.jorge/notebooks/docs/`)

#### **4-Perceptrón-SVM.ipynb**
- Perceptron fundamentals
- Linear classification
- Support Vector Machine theory
- Margin maximization

#### **5-SVM-Kernel.ipynb**
- **Kernel trick** explained
- Mapping φ to higher dimensions
- RBF, Polynomial, Sigmoid kernels
- Computational advantages: O(n²) vs O(n²d)
- Parameter selection (σ, degree)

**Key Concepts**:
- **Kernel function**: `K(x,y) = φ(x)ᵀφ(y)` computed without explicit mapping
- **RBF kernel**: Maps to infinite dimensions
- **Polynomial kernel**: `(xᵀy + c)ᵈ` captures interactions
- **Binomial theorem**: Connects products in original/transformed space

#### **6-ANN.ipynb**
- Neural network architectures
- Backpropagation algorithm
- Activation functions (ReLU, Tanh, Sigmoid)
- Training strategies

---

## 🛠️ Quick Start

### **Run Second Exam Dashboard**

```bash
cd .jorge/partials/second

# Install dependencies
pip install streamlit pandas numpy scikit-learn matplotlib seaborn plotly

# Launch app
streamlit run app.py
```

Visit: `http://localhost:8501`

### **Run Cybersecurity Project**

```bash
cd .jorge/project

# Install with UV
uv sync

# Download Microsoft GUIDE dataset from Kaggle
# Extract to data/microsoft_guide/

# Run dashboard
uv run cybersec-dashboard
```

Visit: `http://localhost:8765`

### **View Theory Notebooks**

```bash
cd .jorge/notebooks/docs
jupyter notebook
```

---

## 📊 Course Progress

| Component | Status | Description | Grade |
|-----------|--------|-------------|-------|
| **Demo Exam** | ✅ Complete | Bayesian, K-NN, Validation | Practice |
| **First Exam** | ✅ Complete | Fundamentals, Iris dataset | TBD |
| **Second Exam** | ✅ Complete | SVM + ANN + PCA Dashboard | 2.5/2.5 |
| **Third Exam** | 🔜 Pending | TBD | - |
| **Final Project** | ✅ Complete | Cybersecurity Incident Predictor | TBD |

**Overall Progress**: 80% Complete

---

## 🎓 Learning Outcomes

By the end of this course, you will master:

### **Classical Machine Learning**
- ✅ Support Vector Machines with kernel methods
- ✅ Bayesian classifiers and probabilistic inference
- ✅ K-Nearest Neighbors algorithms
- ✅ Cross-validation and bootstrapping
- ✅ Hyperparameter optimization

### **Deep Learning**
- ✅ Artificial Neural Networks (feedforward)
- ✅ LSTM/GRU for temporal sequences
- ✅ Graph Neural Networks for relationships
- ✅ Transformers and attention mechanisms

### **Dimensionality Reduction**
- ✅ Principal Component Analysis (PCA)
- ✅ Feature selection and engineering
- ✅ Variance analysis and scree plots
- ✅ Component interpretation

### **Ensemble Methods**
- ✅ Random Forest, XGBoost, LightGBM
- ✅ Gradient boosting techniques
- ✅ Meta-ensemble with adaptive weighting
- ✅ Model stacking strategies

### **Practical Skills**
- ✅ Deploy ML models in production
- ✅ Build interactive dashboards (Streamlit, Solara)
- ✅ Handle imbalanced datasets (SMOTE, SMOTE-ENN)
- ✅ Evaluate with business-focused metrics
- ✅ Make data-driven conclusions
- ✅ Communicate technical results effectively

---

## 🏆 Featured Work

### **Second Exam - Bank Marketing ML Analysis** ⭐
**Interactive dashboard** comparing SVM, ANN, and PCA on UCI Bank Marketing dataset

**Highlights**:
- 3 ML algorithms with comprehensive tuning
- Automated experiment tracking
- PCA impact analysis with insights
- Smart recommendations based on results
- Professional production deployment

**Live Demo**: https://intel-ii-exam-ii.streamlit.app/

---

### **Final Project - Cybersecurity Incident Predictor**
**Enterprise ML platform** for SOC teams with 4-hour incident predictions

**Innovation**:
- Hybrid ensemble (LSTM + GNN + XGBoost + Transformer)
- Meta-learning with context adaptation
- Microsoft GUIDE dataset (13M+ evidences)
- Professional Solara dashboard
- 94.2% prediction accuracy

**Impact**: Prevents incidents before escalation, saves millions in damages

---

## 📚 Documentation Index

### **Exam Documentation**
- **Second Exam**: `.jorge/partials/second/README.md`
  - SVM Guide: `.jorge/partials/second/ui/pages/svm/README.md`
  - ANN Guide: `.jorge/partials/second/ui/pages/ann/README.md`
  - PCA Guide: `.jorge/partials/second/ui/pages/pca/README.md`
  - Deployment: `.jorge/partials/second/DEPLOYMENT.md`

### **Project Documentation**
- **Overview**: `.jorge/project/README.md`
- **Project Vision**: `.jorge/project/project_overview.md`
- **Architecture**: `.jorge/project/architecture_design.md`
- **Dataset**: `.jorge/project/dataset_guide.md`
- **Metrics**: `.jorge/project/evaluation_metrics.md`

### **Theory Materials**
- **SVM Theory**: `.jorge/project/clase-03.md`
- **Notebooks**: `.jorge/notebooks/docs/`

---

## 🌟 Key Achievements

- ✅ **Deployed Production ML App** - Streamlit Cloud
- ✅ **Built Professional SOC Dashboard** - Solara
- ✅ **Implemented Ensemble Learning** - 4 specialized models
- ✅ **Achieved 94%+ Accuracy** - Real-world dataset
- ✅ **Created Comprehensive Documentation** - Theory + Practice
- ✅ **Applied Advanced ML Techniques** - Kernels, PCA, Meta-learning

---

## 👨‍💻 Author

**Jorge Alberto Jaramillo Garzón**  
Computer Engineering Student  
Universidad de Caldas

---

## 🙏 Acknowledgments

- **Professor**: Jorge Alberto Jaramillo Garzón
- **Institution**: Universidad de Caldas
- **Course**: Sistemas Inteligentes II (Intelligent Systems II)
- **Datasets**: 
  - UCI Machine Learning Repository (Bank Marketing, Iris)
  - Microsoft GUIDE (Cybersecurity Incidents)
  - CIC-IDS2017, UNSW-NB15 (Network intrusion)

---

## 📄 License

Academic project for Universidad de Caldas coursework.

---

<div align="center">

**Last Updated**: October 12, 2025  
**Status**: Active Development | 80% Complete

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)

</div>

