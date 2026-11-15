"""Generate and measure candidate powder-particle masks with Meta SAM 2.1."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import re

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.measure import regionprops


MODEL_CONFIG = "configs/sam2.1/sam2.1_hiera_t.yaml"
PIXEL_SIZE = re.compile(
    rb"AP_IMAGE_PIXEL_SIZE\s+Image Pixel Size\s*=\s*"
    rb"([0-9]+(?:\.[0-9]+)?)\s*(nm|(?:\xb5|\xc2\xb5|\xce\xbc|u)m)(?=\s|\x00|$)"
)
PARTICLE_COLUMNS = (
    "image", "particle_id", "centroid_x_px", "centroid_y_px", "area_px2",
    "area_um2", "equivalent_diameter_um", "feret_max_um", "perimeter_um",
    "circularity_2d", "aspect_ratio_major_minor", "solidity",
    "sam_predicted_iou", "sam_stability_score",
)
IMAGE_COLUMNS = (
    "image", "pixel_size_um", "raw_width_px", "raw_height_px", "roi_height_px",
    "sam_candidates", "retained_masks", "rejected_area", "rejected_edge",
    "rejected_overlap", "rejected_disconnected", "median_circularity_2d",
    "diameter_d10_um", "diameter_d50_um", "diameter_d90_um", "status",
)


def pixel_size_um(path: Path) -> float | None:
    """Read Zeiss image pixel spacing in µm/px, including the TIFF's micro-sign encoding."""
    match = PIXEL_SIZE.search(path.read_bytes())
    if match is None:
        return None
    value = float(match[1])
    if value <= 0:
        return None
    return value / 1000 if match[2] == b"nm" else value


def load_field(path: Path, footer_y: int) -> tuple[np.ndarray, tuple[int, int]]:
    with Image.open(path) as image:
        width, height = image.size
        if footer_y and footer_y >= height:
            raise ValueError(f"{path.name}: --footer-y must be below the image height ({height})")
        roi_height = footer_y or height
        cropped = image.crop((0, 0, width, roi_height))
        return np.array(cropped.convert("L").convert("RGB")), (width, height)


def select_masks(candidates, shape, decode, min_area, max_area_fraction):
    """Build a nonoverlapping instance map and record why proposals were rejected."""
    labels = np.zeros(shape, dtype=np.uint16)
    rejected = Counter()
    accepted = []
    max_area = max_area_fraction * labels.size
    connectivity = np.ones((3, 3), dtype=bool)
    ranked = sorted(
        candidates,
        key=lambda item: (item["predicted_iou"], item["stability_score"]),
        reverse=True,
    )
    for candidate in ranked:
        area = candidate["area"]
        if not min_area <= area <= max_area:
            rejected["area"] += 1
            continue

        mask = decode(candidate["segmentation"])
        if mask[0].any() or mask[-1].any() or mask[:, 0].any() or mask[:, -1].any():
            rejected["edge"] += 1
            continue

        ys, xs = np.nonzero(mask)
        box = np.s_[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        local_mask = mask[box]
        local_labels = labels[box]
        occupied = local_labels != 0
        if np.count_nonzero(local_mask & occupied) > 0.03 * area:
            rejected["overlap"] += 1
            continue
        available = local_mask & ~occupied
        if available.sum() < min_area:
            rejected["area"] += 1
            continue
        if ndimage.label(available, structure=connectivity)[1] != 1:
            rejected["disconnected"] += 1
            continue

        label_id = len(accepted) + 1
        if label_id > np.iinfo(labels.dtype).max:
            raise ValueError("Instance count exceeds the 16-bit label image capacity")
        local_labels[available] = label_id
        accepted.append((candidate["predicted_iou"], candidate["stability_score"]))
    return labels, accepted, rejected


def measure_particles(image_name, labels, scores, scale):
    """Compute measurements from the exact label image saved for inspection."""
    rows = []
    for region in regionprops(labels):
        perimeter = region.perimeter_crofton
        center_y, center_x = region.centroid
        predicted_iou, stability = scores[region.label - 1]
        rows.append({
            "image": image_name,
            "particle_id": region.label,
            "centroid_x_px": center_x,
            "centroid_y_px": center_y,
            "area_px2": int(region.area),
            "area_um2": region.area * scale**2 if scale is not None else None,
            "equivalent_diameter_um": (
                region.equivalent_diameter_area * scale if scale is not None else None
            ),
            "feret_max_um": region.feret_diameter_max * scale if scale is not None else None,
            "perimeter_um": perimeter * scale if scale is not None else None,
            "circularity_2d": 4 * math.pi * region.area / perimeter**2 if perimeter else None,
            "aspect_ratio_major_minor": (
                region.axis_major_length / region.axis_minor_length
                if region.axis_minor_length else None
            ),
            "solidity": region.solidity,
            "sam_predicted_iou": predicted_iou,
            "sam_stability_score": stability,
        })
    return rows


def save_overlay(rgb, labels, path):
    rng = np.random.default_rng(41)
    colors = rng.integers(65, 256, size=(int(labels.max()) + 1, 3), dtype=np.uint8)
    foreground = labels > 0
    overlay = rgb.copy()
    overlay[foreground] = np.rint(
        rgb[foreground] * 0.60 + colors[labels[foreground]] * 0.40
    ).astype(np.uint8)
    Image.fromarray(overlay).save(path)


def summarize(path, scale, size, roi_height, num_candidates, rows, rejected):
    diameters = [row["equivalent_diameter_um"] for row in rows if row["equivalent_diameter_um"] is not None]
    circularities = [row["circularity_2d"] for row in rows if row["circularity_2d"] is not None]
    d10, d50, d90 = np.percentile(diameters, [10, 50, 90]) if diameters else (None, None, None)
    return dict(
        image=str(path), pixel_size_um=scale, raw_width_px=size[0], raw_height_px=size[1],
        roi_height_px=roi_height, sam_candidates=num_candidates, retained_masks=len(rows),
        **{f"rejected_{kind}": rejected[kind] for kind in ("area", "edge", "overlap", "disconnected")},
        median_circularity_2d=np.median(circularities) if circularities else None,
        diameter_d10_um=d10, diameter_d50_um=d50, diameter_d90_um=d90,
        status="needs_review" if rows else "no_masks",
    )


def write_csv(path, columns, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", type=Path, nargs="+", help="SEM TIFF files to evaluate")
    parser.add_argument("--checkpoint", type=Path, required=True, help="Official SAM 2.1 Hiera Tiny checkpoint")
    parser.add_argument("--output", type=Path, required=True, help="New directory for masks, previews, and measurements")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda", "mps"), default="auto")
    parser.add_argument("--footer-y", type=int, default=684, help="First row excluded from analysis (0 keeps entire image)")
    parser.add_argument("--points-per-side", type=int, default=24, help="Density of SAM's automatic point grid")
    parser.add_argument("--crop-layers", type=int, choices=(0, 1), default=0, help="Use 1 to add a finer crop pass")
    parser.add_argument("--min-area-px", type=int, default=100)
    parser.add_argument("--max-area-fraction", type=float, default=0.20)
    parser.add_argument("--iou-threshold", type=float, default=0.70, help="SAM-predicted mask quality threshold")
    parser.add_argument("--stability-threshold", type=float, default=0.85)
    args = parser.parse_args(argv)
    if not args.checkpoint.is_file():
        parser.error(f"Checkpoint not found: {args.checkpoint}")
    if args.output.exists():
        parser.error(f"Output directory already exists: {args.output}")
    if args.footer_y < 0 or args.points_per_side < 1 or args.min_area_px < 1:
        parser.error("Use a nonnegative footer row and positive point density and area")
    if not 0 < args.max_area_fraction <= 1:
        parser.error("--max-area-fraction must be in (0, 1]")
    if not 0 <= args.iou_threshold <= 1 or not 0 <= args.stability_threshold <= 1:
        parser.error("Mask thresholds must be in [0, 1]")
    stems = {path.stem.casefold() for path in args.images}
    if len(stems) != len(args.images):
        parser.error("Input images must have distinct basenames for their output files")
    for path in args.images:
        if not path.is_file() or path.suffix.lower() not in {".tif", ".tiff"}:
            parser.error(f"Expected a TIFF file: {path}")
    return args


def main(argv=None):
    args = parse_args(argv)
    import torch
    from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
    from sam2.build_sam import build_sam2
    from sam2.utils.amg import rle_to_mask

    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    model = build_sam2(MODEL_CONFIG, str(args.checkpoint), device=device, apply_postprocessing=False)
    generator = SAM2AutomaticMaskGenerator(
        model,
        points_per_side=args.points_per_side,
        points_per_batch=16,
        pred_iou_thresh=args.iou_threshold,
        stability_score_thresh=args.stability_threshold,
        crop_n_layers=args.crop_layers,
        crop_n_points_downscale_factor=2,
        output_mode="uncompressed_rle",
    )
    args.output.mkdir(parents=True)
    particle_rows = []
    image_rows = []
    for path in args.images:
        rgb, size = load_field(path, args.footer_y)
        scale = pixel_size_um(path)
        print(f"Processing {path}", flush=True)
        with torch.inference_mode():
            candidates = generator.generate(rgb)
        labels, scores, rejected = select_masks(
            candidates, rgb.shape[:2], rle_to_mask, args.min_area_px, args.max_area_fraction
        )
        rows = measure_particles(str(path), labels, scores, scale)
        Image.fromarray(labels).save(args.output / f"{path.stem}_labels.png")
        save_overlay(rgb, labels, args.output / f"{path.stem}_overlay.png")
        particle_rows.extend(rows)
        image_rows.append(summarize(path, scale, size, rgb.shape[0], len(candidates), rows, rejected))
        print(f"  {len(rows)} retained masks from {len(candidates)} SAM proposals", flush=True)

    write_csv(args.output / "particles.csv", PARTICLE_COLUMNS, particle_rows)
    write_csv(args.output / "images.csv", IMAGE_COLUMNS, image_rows)
    settings = vars(args) | {"device": device, "model_config": MODEL_CONFIG, "torch": torch.__version__}
    with args.checkpoint.open("rb") as stream:
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    settings["checkpoint_sha256"] = digest.hexdigest()
    with (args.output / "run.json").open("w", encoding="utf-8") as stream:
        json.dump(settings, stream, indent=2, default=str)
        stream.write("\n")


if __name__ == "__main__":
    main()
