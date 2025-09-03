import argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from paperfig.figure import Fig

FIG_DIR = "fig"

def make_csv_plot_renderer(json_dir: Path):
    """Returns a renderer that plots CSV data as points (optionally with a line)."""
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
        style = str(cfg.get("style", "points")).lower()  # "points" | "line" | "both"
        s = float(cfg.get("marker_size", 18.0))
        alpha = float(cfg.get("alpha", 0.8))
        lw = float(cfg.get("line_width", 1.2))

        arr = np.genfromtxt(path, delimiter=delim, dtype=float)
        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        if x_col >= arr.shape[1] or y_col >= arr.shape[1]:
            raise RuntimeError(f"Figure {index}: column index out of bounds")

        x = arr[:, x_col]
        y = arr[:, y_col]
        if x_max is not None:
            mask = x <= float(x_max)
            x, y = x[mask], y[mask]

        # 散布図（デフォルト）
        fig, ax = plt.subplots(figsize=(4.0, 3.0))
        if style in ("points", "both"):
            ax.scatter(x, y, s=s, alpha=alpha, edgecolor="none")

        # 線（必要なら重ねる）
        if style in ("line", "both"):
            order = np.argsort(x)
            ax.plot(x[order], y[order], lw=lw, color="#444444")

        ax.set_xlabel(f"col {x_col}")
        ax.set_ylabel(f"col {y_col}")
        ax.set_title(data.get("title", path.name))
        ax.grid(True, ls=":", alpha=0.5)

        # 保存
        plt.savefig(f"{FIG_DIR}/fig{index}.pdf")
        plt.close(fig)

        # メタデータ
        return {
            "data_file": str(path),
            "columns": {"x": x_col, "y": y_col},
            "rows": int(arr.shape[0]),
            "style": style,
        }
    return csv_plot

def main():
    p = argparse.ArgumentParser(description="Data-driven figure demo")
    p.add_argument("--json-file", default="fig-data.json")
    p.add_argument("-v", "--verbose", type=int, default=1)
    args = p.parse_args()

    json_dir = Path(args.json_file).expanduser().resolve().parent

    fig = Fig(args.json_file)
    fig.fig_dir = FIG_DIR
    fig.verbose = args.verbose

    # レンダラ登録（json_dir をクロージャで渡す）
    fig.function = {"csv_plot": make_csv_plot_renderer(json_dir)}

    fig.create_pdf()

if __name__ == "__main__":
    main()
