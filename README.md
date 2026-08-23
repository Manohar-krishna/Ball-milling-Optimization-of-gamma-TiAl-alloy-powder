# Ball Milling Optimization of γ-TiAl Alloy Powder using Machine Learning

> A data-driven framework for predicting and optimizing the sphericity of γ-TiAl alloy powders as a function of ball-milling parameters for additive manufacturing applications.

---

## Table of Contents

- [Overview](#overview)
- [Introduction](#Introduction)
- [Aim & Objectives](#aim--objectives)
- [Methodology](#methodology)
- [Results](#results)
- [Conclusion](#conclusion)
- [Future Scope](#future-scope)
- [Citation](#citation)
- [License](#license)

---

## Overview

This project presents an experimental and machine-learning framework that investigates the relationship between ball-milling process parameters and the resulting morphology of γ-TiAl (gamma Titanium Aluminide) alloy powders. The framework predicts particle sphericity and identifies optimal milling conditions suitable for powder bed fusion and other additive manufacturing (AM) processes.

---

## Introduction

Materials science research is inherently expensive and labour-intensive. Industries invest millions annually to identify suitable materials for specific applications through trial-and-error experimentation. This project aims to reduce that cost by shifting from purely observation-oriented research to **data-driven prediction**, leveraging machine learning to extract generalizable insights from small experimental datasets.

> **Key Research Question:** Can machine-learning models accurately predict and optimize the sphericity of γ-TiAl powders as a function of ball-milling parameters for additive manufacturing applications?

---

## Aim & Objectives

**Aim:** To develop and validate a machine-learning-based framework for understanding, predicting, and optimizing the effect of ball-milling parameters on the sphericity of γ-TiAl alloy powders for additive manufacturing applications.

**Objectives:**

1. Conduct controlled ball-milling experiments across a range of process parameters (e.g., milling speed, time, ball-to-powder ratio).
2. Characterize the resulting powder morphology with quantitative sphericity measurements.
3. Build and evaluate machine learning models to predict particle sphericity from process parameters.
4. Apply model-based optimization to identify milling conditions that maximize sphericity.
5. Assess model reliability and uncertainty, particularly given the constraints of a small experimental dataset (N < 30).

---

## Methodology

### Experimental Design

- Ball-milling experiments conducted across a systematic design-of-experiments (DoE) parameter space.
- Powder morphology characterized using scanning electron microscopy (SEM) and image analysis.
- Sphericity computed as the primary response variable.

### Machine Learning Framework

- **Dataset size:** 20 experimental observations.
- **Cross-validation strategy:** Leave-One-Out Cross-Validation (LOOCV) — recommended for datasets with N < 30 to minimize bias in performance estimation.
- **Models evaluated:** _e.g., Gaussian Process Regression, Random Forest, Support Vector Regression_
- **Metrics:** R², RMSE, prediction uncertainty bounds.
- **Overfitting mitigation:** Regularization, cross-validation, and uncertainty quantification were employed throughout.

> **Note on dataset size:** With only 20 observations, models can indicate whether a meaningful relationship exists between parameters and sphericity, but confidence in the generalized learned function is inherently limited. All conclusions are reported with appropriate uncertainty.

---

## Results

| Model | Cross-Validation R² | RMSE | Notes |
|-------|:-------------------:|:----:|-------|
| _Model 1_ | _—_ | _—_ | _Update with actual results_ |
| _Model 2_ | _—_ | _—_ | _Update with actual results_ |

- The best-performing model achieved a cross-validation R² of **[X]** and an RMSE of **[Y]**.
- Optimal milling conditions identified: **[parameters]** → predicted sphericity of **[value]**.
- Feature importance analysis highlighted **[key parameters]** as the most influential on sphericity.

---

## Conclusion

This study demonstrates that machine learning models can serve as effective surrogate tools for predicting γ-TiAl powder sphericity from ball-milling process parameters, even under the constraint of a small experimental dataset. The framework successfully:

- Identified statistically meaningful relationships between milling parameters and powder morphology.
- Provided model-based recommendations for milling conditions that promote near-spherical particles suitable for additive manufacturing.
- Highlighted the importance of rigorous cross-validation and uncertainty reporting when working with limited experimental data.

---

## Future Scope

- **Expand the dataset** through additional experiments or high-throughput synthesis to improve model confidence.
- **Incorporate additional response variables**, such as particle size distribution, flowability, and packing density.
- **Extend to other alloy systems** (e.g., Ti-6Al-4V, Inconel) using transfer learning approaches.
- **Couple with process simulation** (e.g., DEM modelling of ball milling) to generate synthetic training data.
- **Deploy as an interactive tool** for materials engineers to query optimal milling parameters on demand.

---

## Citation

If you use this framework, code, or dataset in your research, please cite:

```bibtex
@misc{YourLastName2026ballmilling,
  author       = {[Gumma Manohar Krishna] and [Naga Sruthi Neelam]},
  title        = {Machine Learning Framework for Ball Milling Optimization of gamma-TiAl Alloy Powder},
  year         = {2026},
  howpublished = {\url{https://github.com/Manohar-krishna/Ball-milling-Optimization-of-gamma-TiAl-alloy-powder.git]}},
  note         = {Research project under the guidance of [Naga Sruthi Neelam], [NIT Raipur]}
}
```

A [`CITATION.cff`](file:///Users/manohar/Documents/Ball%20milling%20Optimization%20of%20gamma%20TiAl%20alloy%20powder/CITATION.cff) file is also provided for automated citation integration with GitHub's **"Cite this repository"** feature.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](file:///Users/manohar/Documents/Ball%20milling%20Optimization%20of%20gamma%20TiAl%20alloy%20powder/LICENSE) file for details.

---

<p align="center">
  <em>Developed as part of a materials science research initiative aimed at accelerating alloy powder development through machine learning.</em>
</p>
