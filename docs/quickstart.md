---
layout: page
title: Quick start
---

This guide shows how to run the bundled example and how to define your own renderer.

## Requirements
- Python 3.9+
- To run the examples: numpy, matplotlib (installed via extras)

## Install
```bash
pip install paperfig
```

For installing with dependencies of examples
```bash
pip install "paperfig[examples]"
```

## Run the example
- Clone the source repository
```bash
git clone https://github.com/sekika/paperfig.git
```
- Change into the examples directory and run the script:
```bash
cd paperfig/docs/examples
python fig.py
```
- Outputs in `docs/examples/fig`:
  - fig1.pdf, fig2.pdf, fig3a.pdf … fig3d.pdf
  - fig3.pdf (2×2 multi‑panel)
  - figures.pdf (all pages concatenated)

## Example files
- Script: [docs/examples/fig.py](https://github.com/sekika/paperfig/blob/main/docs/examples/fig.py)
- JSON spec: [docs/examples/fig.json](https://github.com/sekika/paperfig/blob/main/docs/examples/fig.json)

## Minimal API example
- Define a renderer that writes fig{index}.pdf into the output directory; register and build:

```python
from paperfig.figure import Fig
import matplotlib.pyplot as plt

def render_hello(index, data, verbose=1):
    fig, ax = plt.subplots()
    ax.text(0.5, 0.5, f"Hello {index}", ha="center", va="center")
    plt.savefig(f"out/fig{index}.pdf"); plt.close(fig)

fig = Fig("fig.json")
fig.fig_dir = "out"
fig.function = {"hello": render_hello}
fig.create_pdf()
```

## JSON with a multi‑panel

```json
{
  "1": { "type": "hello" },
  "2": { "type": "hello" },
  "3": {
    "type": "multi",
    "row": 1,
    "column": 2,
    "figures": {
      "3a": { "type": "hello" },
      "3b": { "type": "hello" }
    }
  }
}
```

## Next steps
- [Advanced usage](../advanced/): plotting data from CSV via references in `fig.json`
