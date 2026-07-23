# Overleaf setup for Regime Detection paper

This repository includes the paper source in `paper/paper.tex` and the auto-generated LaTeX tables in `results/paper_results.txt`.

## Recommended Overleaf layout

1. Upload `paper.tex` from the repository root.
2. Upload `paper/paper.tex`.
3. Upload `paper/references.bib`.
4. Upload `results/paper_results.txt`.

## Why this works

- `paper.tex` at the root simply includes `paper/paper.tex`.
- `paper/paper.tex` uses the existing path `../results/paper_results.txt`.
- Overleaf will compile the root `paper.tex` file and find the generated tables automatically.

## Compile command

- In Overleaf, select `paper.tex` as the main file and click Recompile.

## If you want a simpler structure

If you prefer, move `paper/paper.tex` to the project root and update the input line to `\input{results/paper_results.txt}`.
