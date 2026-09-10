# Ball Milling Morphology Analysis of γ-TiAl Alloy Powder

> An SEM-image-based workflow for measuring γ-TiAl powder morphology and establishing reliable experimental labels for future process–property optimization.

---

## Table of Contents

- [Overview](#overview)
- [Research Decision](#research-decision)
- [Aim & Objectives](#aim--objectives)
- [Data Assets](#data-assets)
- [Image-Based Methodology](#image-based-methodology)
- [Findings & Conclusions](#findings--conclusions)
- [Future Scope](#future-scope)
- [Citation](#citation)
- [License](#license)

---

## Overview

This project investigates how ball milling changes the morphology of γ-TiAl alloy powder for additive-manufacturing applications. The current approach prioritizes **SEM-image-based morphology quantification** over direct regression from a small, heterogeneous literature dataset.

Rather than claiming a process-parameter model can already identify optimal milling conditions, the project uses SEM images to measure morphology directly: projected circularity, particle size, aspect ratio, solidity, agglomeration, and the fraction of particles meeting a declared near-spherical criterion. These image-derived measurements provide traceable labels for later process–property modeling.

## Research Decision

The literature dataset is retained as contextual evidence, but it is not used as the primary source for Ridge, Support Vector Regression (SVR), or Gaussian Process Regression (GPR) process models.

The dataset contains only 20 heterogeneous records. Several records summarize a range of milling conditions rather than a single experiment; alloy compositions, mill types, and post-processing states differ; and the reported outcomes do not provide a consistent sphericity target. Important milling descriptors—including jar geometry, ball size and material, powder loading, process-control agent, atmosphere, and milling medium—are incomplete or absent.

Under these conditions, weak generalization from Ridge, SVR, and GPR is expected:

- **Ridge regression** assumes one approximately linear relationship across studies with incompatible experimental configurations.
- **SVR** is sensitive to feature scaling, kernel choice, and hyperparameters when there are few independent observations.
- **GPR** requires enough comparable observations to estimate a smooth process–property relationship and its uncertainty; with sparse, heterogeneous data, kernel and noise estimates are unstable.

This is a limitation of the available evidence, not a claim that these methods are unsuitable for well-designed experimental datasets. The repository therefore avoids reporting unsupported R², RMSE, or optimal-condition claims.

## Aim & Objectives

**Aim:** To build a reproducible SEM-image-analysis workflow that quantifies γ-TiAl powder morphology after ball milling and produces experimentally grounded morphology labels.

**Objectives:**

1. Catalogue SEM images with batch, processing-condition, and calibration metadata.
2. Identify image fields suitable for individual-particle morphology analysis.
3. Segment particles and measure projected circularity, equivalent diameter, aspect ratio, solidity, and related shape descriptors.
4. Aggregate particle-level measurements by image and then by independently prepared milling condition.
5. Compare experimental image groups with the atomised-powder baseline, subject to confirmation of comparable composition and acquisition conditions.
6. Use the resulting condition-level morphology data to design future controlled ball-milling experiments.

## Data Assets

| Asset | Contents | Intended use |
|---|---:|---|
| `Data/Literature Data/TiAl_Ball_Milling_raw_dataset.csv` | 20 literature records | Context, provenance review, and experimental-design guidance; not a standalone sphericity-training dataset. |
| `Data/Experiment Data/` | 39 SEM TIFF images in 24 h, 48 h, and 72 h-labelled groups | Experimental morphology quantification. Group labels must be verified against lab records. |
| `Data/Ti Atomised/` | 12 SEM TIFF images | Atomised-powder morphology baseline. Composition must be confirmed before treating it as a γ-TiAl control. |
| `Data/Processed/` | Processed tabular datasets | Intermediate, traceable data-processing outputs. |

The image files are technical fields of view and magnifications, not automatically independent experiments. Multiple images from the same batch or condition must remain grouped during analysis and validation.

## Image-Based Methodology

### 1. Build an image manifest

Create one manifest row per TIFF image containing `image_id`, file path, batch or condition ID, composition, milling time, RPM, BPR, mill type, medium, pixel size, magnification, image type, and usability status. Do not infer missing processing information from filenames alone.

### 2. Select and calibrate images

Classify images as isolated powder, touching powder, agglomerated powder, compacted/surface morphology, or unsuitable. Use the embedded SEM calibration and verify it against the scale bar. Crop or mask the instrument footer, scale bar, and logo before analysis without modifying the raw TIFF files.

### 3. Segment individual particles

Use a documented segmentation workflow, such as background correction, conservative thresholding, distance transform, and watershed separation for touching particles. Review particle-mask overlays against each original SEM image. Manually assess a representative subset to quantify missed, merged, or falsely split particles.

### 4. Calculate morphology features

For each accepted particle, calculate:

- projected circularity: \(4πA / P^2\);
- equivalent circular diameter;
- aspect ratio and Feret diameter;
- solidity and convexity;
- exclusion flags for border-touching, unresolved, or artefactual objects.

The resulting measurement is **2D projected circularity**, not 3D sphericity. A near-spherical threshold must be chosen before group comparisons and reported with the results.

### 5. Aggregate and compare

Summarize particle measurements first by SEM field and then by independent milling condition. Use robust summaries such as median, interquartile range, D10/D50/D90, and fraction above the circularity threshold. Do not treat particles or images from one condition as independent process experiments.

### 6. Validate responsibly

Validate segmentation against manual checks and retain image, batch, and condition identifiers throughout. Any future predictive model must use grouped validation that holds out whole batches or conditions; it must not split particles from a single image across training and test sets.

## Findings & Conclusions

The current evidence supports the following conclusions:

1. The literature dataset is too small, heterogeneous, and incompletely described for reliable process-parameter optimization with Ridge, SVR, or GPR.
2. Its records do not supply a consistent, condition-level sphericity target, so model metrics or proposed optimal milling conditions would not be scientifically supported.
3. SEM images contain direct evidence of the morphology relevant to powder processing and additive manufacturing.
4. Image analysis can create traceable, condition-level morphology labels from real powder particles.
5. Image fields and particles are technical replicates; they improve morphological measurement precision but do not increase the number of independent milling experiments.
6. A valid future process–property model requires additional controlled milling batches with complete processing metadata and image-derived morphology labels.

## Future Scope

- Complete the image manifest by linking every SEM image to verified laboratory conditions.
- Establish and validate an annotated particle-segmentation workflow.
- Compare atomised and milled powder only after chemistry and sampling comparability are confirmed.
- Expand the number of independently prepared milling conditions across a planned design of experiments.
- Use image-derived circularity and size-distribution summaries as model targets once sufficient independent conditions are available.
- Evaluate process–property models with study-, batch-, or condition-grouped validation and report uncertainty on held-out real experiments.

---

## Citation

If you use this framework, code, or dataset in your research, please cite:

```bibtex
@misc{Gumma2026ballmilling,
  author       = {[Gumma Manohar Krishna] and [Naga Sruthi Neelam]},
  title        = {Machine Learning Framework for Ball Milling Optimization of gamma-TiAl Alloy Powder},
  year         = {2026},
  howpublished = {\url{https://github.com/Manohar-krishna/Ball-milling-Optimization-of-gamma-TiAl-alloy-powder.git}},
  note         = {Research project under the guidance of [Naga Sruthi Neelam], [NIT Raipur]}
}
```

A [CITATION.cff](CITATION.cff) file is also provided for GitHub's **"Cite this repository"** feature.

---

## License

This project is licensed under the **MIT License** — see [License](License) for details.

---

<p align="center">
  <em>Developed as part of a materials-science research initiative to establish reliable powder-morphology evidence for future data-driven optimization.</em>
</p>
