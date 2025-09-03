---
layout: page
title: Advanced
---

This page shows how to pass data references (e.g., file paths) in fig.json and use them in renderers to plot measured data points. The example resolves paths relative to the JSON file and supports multi‑panel compositions.

## What’s included
- Renderer and runner: [docs/examples/fig_data.py](https://github.com/sekika/paperfig/blob/main/docs/examples/fig-data.py)
- JSON spec: [docs/examples/fig-data.json](https://github.com/sekika/paperfig/blob/main/docs/examples/fig-data.json)
- Sample data (headerless CSV):
  - [docs/examples/data/sensor_a.csv](https://github.com/sekika/paperfig/blob/main/docs/examples/data/sensor_a.csv) (time, value; noisy upward trend)
  - [docs/examples/data/sensor_b.csv](https://github.com/sekika/paperfig/blob/main/docs/examples/data/sensor_b.csv) (time, series1, series2; noisy oscillatory series)

## Renderer and runner (csv_plot)
- The renderer plots points from a CSV, with optional line overlay, and returns metadata. It resolves data paths relative to the JSON location.

```python
# docs/examples/fig_data.py
import argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from paperfig.figure import Fig

FIG_DIR = "fig"

def make_csv_plot_renderer(json_dir: Path):
    def csv_plot(index, data, verbose=1):
        cfg = data.get("data", {})
        if not isinstance(cfg, dict):
            raise RuntimeError(f"Figure {index}: 'data' must be an object")
        rel = cfg.get("file")
        if not rel:
            raise RuntimeError(f"Figure {index}: 'data.file' is required")
        path = (json_dir / rel).expanduser().resolve()
        if not path.exists():
            raise RuntimeError(f"Figure {index}: data file not found: {path}")

        delim = cfg.get("delimiter", ",")
        x_col = int(cfg.get("x_col", 0))
        y_col = int(cfg.get("y_col", 1))
        x_max = cfg.get("x_max", None)
        style = str(cfg.get("style", "points")).lower()  # points | line | both
        s = float(cfg.get("marker_size", 18.0))
        alpha = float(cfg.get("alpha", 0.8))
        lw = float(cfg.get("line_width", 1.2))

        arr = np.genfromtxt(path, delimiter=delim, dtype=float)
        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        if x_col >= arr.shape[1] or y_col >= arr.shape[1]:
            raise RuntimeError(f"Figure {index}: column index out of bounds")
        x = arr[:, x_col]; y = arr[:, y_col]
        if x_max is not None:
            mask = x <= float(x_max)
            x, y = x[mask], y[mask]

        fig, ax = plt.subplots(figsize=(4.0, 3.0))
        if style in ("points", "both"):
            ax.scatter(x, y, s=s, alpha=alpha, edgecolor="none")
        if style in ("line", "both"):
            order = np.argsort(x)
            ax.plot(x[order], y[order], lw=lw, color="#444444")

        ax.set_xlabel(f"col {x_col}")
        ax.set_ylabel(f"col {y_col}")
        ax.set_title(data.get("title", path.name))
        ax.grid(True, ls=":", alpha=0.5)

        plt.savefig(f"{FIG_DIR}/fig{index}.pdf"); plt.close(fig)
        return {"data_file": str(path), "columns": {"x": x_col, "y": y_col},
                "rows": int(arr.shape[0]), "style": style}
    return csv_plot

def main():
    p = argparse.ArgumentParser(description="Data-driven figure demo")
    p.add_argument("--json-file", default="fig-data.json")
    p.add_argument("-v", "--verbose", type=int, default=1)
    args = p.parse_args()

    json_dir = Path(args.json_file).expanduser().resolve().parent
    fig = Fig(args.json_file); fig.fig_dir = FIG_DIR; fig.verbose = args.verbose
    fig.function = {"csv_plot": make_csv_plot_renderer(json_dir)}
    fig.create_pdf()

if __name__ == "__main__":
    main()
```

## JSON spec referencing CSVs
- Use per‑figure data keys for file paths and plotting options. style can be "points" (default), "line", or "both". Use x_max to zoom in multi panels.

```json
{
  "1": {
    "type": "csv_plot",
    "title": "Sensor A (points)",
    "data": { "file": "data/sensor_a.csv", "x_col": 0, "y_col": 1, "delimiter": ",", "style": "points" }
  },
  "2": {
    "type": "csv_plot",
    "title": "Sensor B (points)",
    "data": { "file": "data/sensor_b.csv", "x_col": 0, "y_col": 2, "delimiter": ",", "style": "points" }
  },
  "3": {
    "type": "multi",
    "row": 1,
    "column": 2,
    "figures": {
      "3a": {
        "type": "csv_plot",
        "title": "A zoomed (points)",
        "data": { "file": "data/sensor_a.csv", "x_col": 0, "y_col": 1, "delimiter": ",", "style": "points", "x_max": 100 }
      },
      "3b": {
        "type": "csv_plot",
        "title": "B zoomed (points)",
        "data": { "file": "data/sensor_b.csv", "x_col": 0, "y_col": 2, "delimiter": ",", "style": "points", "x_max": 100 }
      }
    }
  }
}
```

## Sample data
- Headerless CSVs in docs/examples/data:
  - sensor_a.csv — two columns: time, value (noisy trend)
  - sensor_b.csv — three columns: time, series1, series2 (we plot series2 with y_col=2)

## Run the advanced example
- From the repo root:
```bash
cd docs/examples
python fig_data.py
```
- Outputs in docs/examples/fig:
  - `fig1.pdf` (sensor_a points), `fig2.pdf` (sensor_b points)
  - `fig3a.pdf`, `fig3b.pdf` (zoomed)
  - `fig3.pdf` (1×2 multi panel)
  - `figures.pdf` (all concatenated)

## Tips and best practices
- Resolve paths relative to the JSON file directory for reproducible runs.
- Validate inputs early (missing files, wrong columns) and raise clear errors; paperfig will surface them with the figure id.
- Return metadata (data_file, columns, rows, style) or the calculation result for future use; you can later refer to it by fig.result.
- To reuse the same input file across multiple panels, keep data.file identical and vary only plotting options (y_col, x_max, styles).

## Using the CLI with dynamic imports
- If you package csv_plot in your own module, you can reference it in JSON and use the CLI:
  - JSON: { "type": "yourpkg.renderers:csv_plot", "data": { "file": "/abs/path/sensor_a.csv", ... } }
  - Build: `paperfig build docs/examples/fig-data.json -d out`
- Note: injecting the JSON directory path into dynamically imported renderers is non‑trivial. Prefer absolute paths in JSON, or use a thin wrapper script (like fig_data.py) to bind json_dir via a closure.
