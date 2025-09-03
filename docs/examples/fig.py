#!/usr/bin/env python
import argparse
import numpy as np
import matplotlib.pyplot as plt
from paperfig.figure import Fig

FIG_DIR = "fig"


def render_sine(index, data, verbose=1):
    A = float(data.get("amplitude", 1.0))
    f = float(data.get("frequency", 1.0))
    samples = int(data.get("samples", 500))
    noise = float(data.get("noise", 0.0))
    damping = float(data.get("damping", 0.0))
    title = data.get("title", f"Sine: A={A}, f={f}")

    t = np.linspace(0, 2 * np.pi, samples)
    y = A * np.sin(2 * np.pi * f * t)
    if damping > 0:
        y = y * np.exp(-damping * t)
    if noise > 0:
        rng = np.random.default_rng(int(data.get("seed", 0)))
        y = y + noise * rng.standard_normal(size=t.shape)

    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    ax.plot(t, y, lw=1.8)
    ax.set_xlabel("t")
    ax.set_ylabel("y")
    ax.set_title(title)
    ax.grid(True, ls=":", alpha=0.6)

    plt.savefig(f"{FIG_DIR}/fig{index}.pdf")
    plt.close(fig)
    return {"summary": {"amplitude": A, "frequency": f}}


def render_scatter(index, data, verbose=1):
    n = int(data.get("n", 300))
    rho = float(data.get("rho", 0.0))
    seed = int(data.get("seed", 0))
    title = data.get("title", f"Scatter: n={n}, rho={rho}")

    rng = np.random.default_rng(seed)
    mean = np.array([0.0, 0.0])
    cov = np.array([[1.0, rho], [rho, 1.0]])
    xy = rng.multivariate_normal(mean, cov, size=n)

    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    ax.scatter(xy[:, 0], xy[:, 1], s=12, alpha=0.7)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(title)
    ax.grid(True, ls=":", alpha=0.4)
    ax.axis("equal")

    plt.savefig(f"{FIG_DIR}/fig{index}.pdf")
    plt.close(fig)
    return {"summary": {"n": n, "rho": rho}}


def render_hist(index, data, verbose=1):
    n = int(data.get("n", 1000))
    bins = int(data.get("bins", 30))
    dist = data.get("dist", "normal")
    seed = int(data.get("seed", 0))
    title = data.get("title", f"Histogram: {dist}, n={n}")

    rng = np.random.default_rng(seed)
    if dist == "uniform":
        x = rng.uniform(-1, 1, size=n)
    else:
        x = rng.standard_normal(size=n)

    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    ax.hist(x, bins=bins, color="#4472C4", alpha=0.85, edgecolor="white")
    ax.set_xlabel("value")
    ax.set_ylabel("count")
    ax.set_title(title)
    ax.grid(True, axis="y", ls=":", alpha=0.5)

    plt.savefig(f"{FIG_DIR}/fig{index}.pdf")
    plt.close(fig)
    return {"summary": {"n": n, "bins": bins, "dist": dist}}


def main():
    parser = argparse.ArgumentParser(description="Simple figure generator demo")
    parser.add_argument("--json-file", type=str, default="fig.json", help="JSON spec file")
    parser.add_argument("-v", "--verbose", type=int, default=1, help="verbosity (0/1/2)")
    args = parser.parse_args()

    fig = Fig(args.json_file)
    fig.fig_dir = FIG_DIR
    fig.verbose = args.verbose
    fig.function = {"sine": render_sine, "scatter": render_scatter, "hist": render_hist}
    fig.create_pdf()


if __name__ == "__main__":
    main()