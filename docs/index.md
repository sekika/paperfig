---
layout: page
title: paperfig
---
`paperfig` is a small library for building per-figure PDFs from a JSON spec and combining them into a single figures.pdf. The JSON file can mix data and rendering functions, so you can flexibly compose plots and layouts. This makes it handy for generating figures for papers. You provide the renderers (Python functions that draw and save fig{index}.pdf), while paperfig takes care of JSON parsing, dispatching, multi-panel layouts, and concatenation.

## Features
- Simple JSON spec → figures
- Use your own renderers; paperfig only orchestrates
- Supports both simple figures and multi‑panel grids
- Concatenates everything into a single figures.pdf
- Extensible: register functions, import "module:function", or use entry points

## Install
- Library: `pip install paperfig`
- With example dependencies: `pip install "paperfig[examples]"`

## Command‑line
- Build: `paperfig build path/to/fig.json -d out -o figures.pdf`
- Validate: `paperfig validate path/to/fig.json`
- List: paperfig list `path/to/fig.json`

## Get started
- [Quick start](quickstart/)
- [Advanced](advanced/): data‑driven figures and reusable renderers
- Example files live under [docs/examples](https://github.com/sekika/paperfig/tree/main/docs/examples) in the repository
