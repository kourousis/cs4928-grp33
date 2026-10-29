"""
CS4928 G33 / P32 - RQ3 duplication, size and re-run-fault measure (task 8c; reused by 9c).

Measures the analysis code at a git ref (default PRE_EVENT_A, the state before any RQ3
change), so the same numbers can be taken again after the refactor and compared:

    size        per file: cells, code lines, SLOC (physical lines with code, after
                dropping blank and comment-only lines), logical lines (statements; a
                statement split over several physical lines counts once), defined functions
    functions   every top-level function, grouped by name across files: in how many
                files it appears and whether the copies are identical (same AST, so
                comments, spacing and the docstring are ignored). A different AST is not
                necessarily different behaviour; that has to be judged by reading the copies
    clones      cross-file duplicated logical lines: a logical line counts as duplicated
                when it lies inside a run of WINDOW (default 5) consecutive normalised
                logical lines that also occurs in another file. Lines are normalised to their
                tokens, so comments and spacing do not matter but names do (exact, "type-1"
                clones: a copy with renamed variables is not found). Runs never cross a
                notebook cell boundary, so cells shorter than WINDOW never count. The share
                is therefore a lower bound
    faults      evidence for the re-run faults named in M1_PLAN.md § RQ3: the data path
                each file reads (R1), names used but never defined or imported (R2), and
                random-number calls in a file with no seed. Limits, by design:
                - data paths are found only as a literal first argument of read_csv; a path
                  built from variables is not reported, so an empty list proves nothing
                - a seed counts only as a seed()/default_rng()/RandomState() call with a
                  literal, non-None argument in the same file; default_rng(seed) with a
                  variable counts as an unseeded random source. Seeding passed in from
                  another file is not followed, so such a file must be judged by reading it

    python repro/rq3_measure.py                                  # the four notebooks at PRE_EVENT_A
    python repro/rq3_measure.py --ref FINAL frequentist/stats.py frequentist/*.ipynb
    python repro/rq3_measure.py --worktree ...                   # read files from disk instead

.ipynb files are measured on their code cells only (IPython magic and shell lines are
blanked first), .py files whole. Writes to
repro/rq3_measure/<UTC timestamp>/:
    measure.json        every number, per file and in total
    measure.txt         the same, human-readable
    environment.txt     python version (kept out of the other files so a different patch
                        release doesn't make check_fresh_clone.py report a difference)
    inputs_sha256.txt   hashes of every file read (as read, CRLF -> LF), and this script
"""
import argparse
import ast
import builtins
import hashlib
import io
import json
import platform
import subprocess
import sys
import tokenize
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_REF = "PRE_EVENT_A"
DEFAULT_FILES = [
    "frequentist/codehealth.ipynb",
    "frequentist/completion_time.ipynb",
    "frequentist/coverage.ipynb",
    "frequentist/perceived_productivity.ipynb",
]
WINDOW = 5
# Names IPython provides in every notebook kernel without an import.
KERNEL_NAMES = {"display", "get_ipython", "In", "Out", "exit", "quit"}
RANDOM_PREFIXES = ("np.random.", "numpy.random.", "random.")
SEED_CALLS = {"np.random.seed", "numpy.random.seed", "random.seed"}
RNG_CALLS = {"np.random.default_rng", "numpy.random.default_rng", "np.random.RandomState",
             "numpy.random.RandomState"}


def read_text(rel, ref):
    """The file's text at `ref` (None = working tree), with CRLF turned into LF."""
    if ref is None:
        raw = (REPO / rel).read_bytes()
    else:
        res = subprocess.run(["git", "-C", str(REPO), "show", f"{ref}:{rel}"], capture_output=True)
        if res.returncode:
            raise SystemExit(f"{rel} not found at {ref}: {res.stderr.decode().strip()}")
        raw = res.stdout
    return raw.replace(b"\r\n", b"\n").decode("utf-8")


def code_cells(rel, text):
    """The file as a list of code blocks (one per code cell for a notebook, one for a .py file),
    their 0-based positions among all the notebook's cells (None for a .py file), and the cell count."""
    if rel.endswith(".ipynb"):
        nb = json.loads(text)
        cells, positions = [], []
        for pos, cell in enumerate(nb["cells"]):
            if cell["cell_type"] == "code":
                src = cell["source"]
                src = "".join(src) if isinstance(src, list) else src
                # IPython magics and shell lines (%..., !...) aren't Python: blank them, keeping line numbers.
                cells.append("".join("\n" if ln.lstrip().startswith(("%", "!")) else ln
                                     for ln in src.splitlines(keepends=True)))
                positions.append(pos)
        return cells, positions, len(nb["cells"])
    return [text], [None], None


def norm_lines(source):
    """Token-normalised code lines of one block: [(line number, normalised text)], with
    blank and comment-only lines dropped. A line continued over several physical lines is
    kept as one logical line, numbered by its first line."""
    out, toks, start = [], [], None
    skip = {tokenize.COMMENT, tokenize.NL, tokenize.INDENT, tokenize.DEDENT,
            tokenize.ENCODING, tokenize.ENDMARKER}
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.NEWLINE:
            if toks:
                out.append((start, " ".join(toks)))
            toks, start = [], None
        elif tok.type not in skip:
            if start is None:
                start = tok.start[0]
            toks.append(tok.string)
    if toks:
        out.append((start, " ".join(toks)))
    return out


def sloc_lines(source):
    """Physical line numbers that hold code (not blank, not only a comment)."""
    lines = set()
    skip = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT,
            tokenize.ENCODING, tokenize.ENDMARKER}
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type not in skip:
            lines.update(range(tok.start[0], tok.end[0] + 1))
    return lines


def dotted(node):
    """'np.random.choice' for an attribute chain of names, else None."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def strip_docstring(fn):
    body = fn.body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:]
    return ast.dump(ast.Module(body=body, type_ignores=[]), include_attributes=False) + ast.dump(fn.args)


def literal_seed(call):
    """True if the call's first argument (or its `seed` keyword) is a literal other than None."""
    args = list(call.args[:1]) + [k.value for k in call.keywords if k.arg == "seed"]
    return any(isinstance(a, ast.Constant) and a.value is not None for a in args)


def bound_names(tree):
    """Every name the code binds anywhere: assignments, imports, defs, loop/with/except
    targets and parameters. Coarse (ignores scope and order), so it can only under-report."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            names.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
    return names


def analyse_file(rel, text):
    cells, positions, n_cells = code_cells(rel, text)
    trees = [ast.parse(c) for c in cells]
    whole = ast.Module(body=[n for t in trees for n in t.body], type_ignores=[])

    functions = []
    for pos, src, tree in zip(positions, cells, trees):
        lines = sloc_lines(src)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                span = range(node.lineno, node.end_lineno + 1)
                functions.append({"name": node.name, "cell": pos,
                                  "sloc": sum(1 for ln in span if ln in lines),
                                  "ast": strip_docstring(node)})

    bound = bound_names(whole)
    undefined = sorted({n.id for n in ast.walk(whole)
                        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
                        and n.id not in bound and n.id not in KERNEL_NAMES and not hasattr(builtins, n.id)})

    data_paths, random_calls, seeds = [], defaultdict(int), []
    for node in ast.walk(whole):
        if not isinstance(node, ast.Call):
            continue
        name = dotted(node.func) or ""
        if name.endswith("read_csv") and node.args and isinstance(node.args[0], ast.Constant):
            data_paths.append(node.args[0].value)
        if (name in SEED_CALLS or name in RNG_CALLS) and literal_seed(node):
            seeds.append(name)
        elif name.startswith(RANDOM_PREFIXES):  # includes seed() / a generator without a literal seed
            random_calls[name] += 1

    return {
        "cells": n_cells,
        "code_cells": len(cells) if n_cells is not None else None,
        "code_lines": sum(len(c.splitlines()) for c in cells),
        "sloc": sum(len(sloc_lines(c)) for c in cells),
        "functions": functions,
        "faults": {"data_paths": data_paths, "undefined_names": undefined,
                   "random_calls": dict(sorted(random_calls.items())), "seed_calls": seeds,
                   "unseeded_random": bool(random_calls) and not seeds},
        "_cells": cells,
    }


def clone_lines(files, window):
    """For each file, the set of (cell, line) positions inside a run of `window` normalised
    lines that also occurs in a different file."""
    runs = {}  # file -> list of (key, positions)
    owners = defaultdict(set)
    for rel, info in files.items():
        runs[rel] = []
        for cell_no, src in enumerate(info["_cells"]):
            lines = norm_lines(src)
            for i in range(len(lines) - window + 1):
                chunk = lines[i:i + window]
                key = "\n".join(t for _, t in chunk)
                runs[rel].append((key, [(cell_no, ln) for ln, _ in chunk]))
                owners[key].add(rel)
    dup = {}
    for rel, items in runs.items():
        hit = set()
        for key, pos in items:
            if len(owners[key]) > 1:
                hit.update(pos)
        dup[rel] = hit
    return dup


def function_groups(files):
    by_name = defaultdict(list)
    for rel, info in files.items():
        for fn in info["functions"]:
            by_name[fn["name"]].append((rel, fn))
    groups = []
    for name, copies in sorted(by_name.items()):
        variants = sorted({fn["ast"] for _, fn in copies})
        groups.append({
            "name": name,
            "files": [rel for rel, _ in copies],
            "copies": len(copies),
            "in_files": len({rel for rel, _ in copies}),
            "sloc_each": [fn["sloc"] for _, fn in copies],
            "variants": len(variants),
            "variant_each": [variants.index(fn["ast"]) for _, fn in copies],
        })
    return groups


def measure(paths, ref, window):
    texts = {rel: read_text(rel, ref) for rel in paths}
    files = {rel: analyse_file(rel, t) for rel, t in texts.items()}
    dup = clone_lines(files, window)
    for rel, info in files.items():
        # Duplication is counted in logical lines, on both sides of the share.
        logical = sum(len(norm_lines(c)) for c in info["_cells"])
        info["logical_lines"] = logical
        info["duplicated_logical_lines"] = len(dup[rel])
        info["duplicated_share"] = round(len(dup[rel]) / logical, 4) if logical else 0.0
    groups = function_groups(files)
    copied = [g for g in groups if g["in_files"] > 1]
    total_logical = sum(f["logical_lines"] for f in files.values())
    total_dup = sum(f["duplicated_logical_lines"] for f in files.values())
    totals = {
        "files": len(files),
        "code_lines": sum(f["code_lines"] for f in files.values()),
        "sloc": sum(f["sloc"] for f in files.values()),
        "logical_lines": total_logical,
        "duplicated_logical_lines": total_dup,
        "duplicated_share": round(total_dup / total_logical, 4) if total_logical else 0.0,
        "functions_defined": sum(len(f["functions"]) for f in files.values()),
        "distinct_function_names": len(groups),
        "functions_copied_across_files": len(copied),
        "copied_function_sloc": sum(sum(g["sloc_each"]) for g in copied),
        "copied_functions_not_identical": [g["name"] for g in copied if g["variants"] > 1],
        "files_with_undefined_names": [r for r, f in files.items() if f["faults"]["undefined_names"]],
        "files_with_unseeded_random": [r for r, f in files.items() if f["faults"]["unseeded_random"]],
        "distinct_data_path_prefixes": sorted({p.rsplit("/", 1)[0] + "/" for f in files.values()
                                               for p in f["faults"]["data_paths"] if "/" in p}),
    }
    for f in files.values():
        del f["_cells"]
        for fn in f["functions"]:
            del fn["ast"]
    return texts, files, groups, totals


def report(meta, files, groups, totals):
    w = []
    w.append(f"RQ3 measure at {meta['ref']} ({meta['commit']}), window = {meta['window']} lines")
    w.append(f"run {meta['run_utc']}")
    w.append("")
    w.append(f"{'file':42} {'cells':>5} {'lines':>5} {'SLOC':>5} {'logic':>5} {'defs':>4} {'dup':>5} {'dup%':>6}")
    for rel, f in files.items():
        cells = "-" if f["cells"] is None else f"{f['code_cells']}/{f['cells']}"
        w.append(f"{rel:42} {cells:>5} {f['code_lines']:>5} {f['sloc']:>5} {f['logical_lines']:>5} "
                 f"{len(f['functions']):>4} "
                 f"{f['duplicated_logical_lines']:>5} {100 * f['duplicated_share']:>5.1f}%")
    t = totals
    w.append(f"{'TOTAL':42} {'':>5} {t['code_lines']:>5} {t['sloc']:>5} {t['logical_lines']:>5} "
             f"{t['functions_defined']:>4} "
             f"{t['duplicated_logical_lines']:>5} {100 * t['duplicated_share']:>5.1f}%")
    w.append("  cells = code cells / all cells; logic = logical lines (statements); "
             "dup = logical lines in a cross-file clone run; dup% = dup / logic")
    w.append("")
    w.append("Functions defined in more than one file:")
    for g in groups:
        if g["in_files"] > 1:
            state = "identical" if g["variants"] == 1 else f"{g['variants']} AST versions"
            where = ", ".join(f"{Path(r).stem}[v{v}]" if g["variants"] > 1 else Path(r).stem
                              for r, v in zip(g["files"], g["variant_each"]))
            w.append(f"  {g['name']:32} x{g['copies']}  {state:22} SLOC {g['sloc_each']}  ({where})")
    singles = [g["name"] for g in groups if g["in_files"] == 1]
    w.append(f"Functions in one file only: {', '.join(singles) or '-'}")
    w.append(f"Copied functions: {t['functions_copied_across_files']} names, "
             f"{t['copied_function_sloc']} SLOC in all copies")
    w.append("")
    w.append("Re-run faults:")
    for rel, f in files.items():
        fl = f["faults"]
        rnd = ", ".join(f"{k} x{v}" for k, v in fl["random_calls"].items()) or "none"
        w.append(f"  {Path(rel).name}")
        w.append(f"    data paths:       {fl['data_paths'] or '-'}")
        w.append(f"    undefined names:  {fl['undefined_names'] or '-'}")
        w.append(f"    random calls:     {rnd}; seeds: {fl['seed_calls'] or 'none'}"
                 f"{'  -> UNSEEDED' if fl['unseeded_random'] else ''}")
    w.append(f"  data path prefixes in use: {t['distinct_data_path_prefixes']}")
    return "\n".join(w) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", default=DEFAULT_FILES, help="repo-relative .ipynb / .py files")
    ap.add_argument("--ref", default=DEFAULT_REF, help="git ref to read the files at (default PRE_EVENT_A)")
    ap.add_argument("--worktree", action="store_true", help="read the files from disk instead of a git ref")
    ap.add_argument("--window", type=int, default=WINDOW, help="clone run length in logical lines")
    args = ap.parse_args()

    ref = None if args.worktree else args.ref
    commit = "WORKTREE" if ref is None else subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", f"{ref}^{{commit}}"],
        capture_output=True, text=True, check=True).stdout.strip()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    meta = {"task": "8c", "ref": ref or "WORKTREE", "commit": commit, "window": args.window,
            "files": args.files, "run_utc": stamp}

    texts, files, groups, totals = measure(args.files, ref, args.window)

    out = REPO / "repro" / "rq3_measure" / stamp
    out.mkdir(parents=True)
    (out / "measure.json").write_text(json.dumps({"meta": meta, "totals": totals, "files": files,
                                                  "function_groups": groups}, indent=2) + "\n",
                                      encoding="utf-8")
    text = report(meta, files, groups, totals)
    (out / "measure.txt").write_text(text, encoding="utf-8")
    (out / "environment.txt").write_text(f"python {platform.python_version()}\n{sys.version}\n",
                                         encoding="utf-8")
    with open(out / "inputs_sha256.txt", "w", encoding="utf-8") as f:
        for rel, t in texts.items():
            f.write(f"{hashlib.sha256(t.encode('utf-8')).hexdigest()}  {rel} @ {meta['ref']}\n")
        script = Path(__file__).resolve()
        digest = hashlib.sha256(script.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        f.write(f"{digest}  {script.relative_to(REPO).as_posix()}\n")
    print(text, end="")
    print(f"wrote {out.relative_to(REPO).as_posix()}")


if __name__ == "__main__":
    main()
