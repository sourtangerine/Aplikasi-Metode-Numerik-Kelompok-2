# Trapezoid Rule Integration (Criterion 1)

A single-file Python program (`main.py`) that integrates a function with the
**trapezoid rule**, shows every step of the solution, and tells you whether the
method works for the function and how many segments it needs.

It reproduces *Aturan Trapesium - Contoh 21.1* from the lecture slides:

    f(x) = 0.2 + 25x - 200x^2 + 675x^3 - 900x^4 + 400x^5,   a = 0,  b = 0.8
    analytic integral = 1.640533

## Requirements

- Python 3.8 or newer
- No extra packages (standard library only)

## Quick start

Put `main.py` anywhere and run it from that folder:

    python main.py                # slide example, single segment (n = 1)
    python main.py --n 1 10       # single segment, then 10 segments
    python main.py --b 1.2 --n 10 # change the upper limit to 1.2

## Options

| Option | Meaning | Default |
|---|---|---|
| `--a`, `--b` | lower / upper integration limit | `0`, `0.8` |
| `--n` | one or more segment counts to solve step by step | `1` |
| `--coeffs` | polynomial coefficients, ascending powers (`c0 c1 c2 ...`) | the slide function |
| `--expr` | any expression in `x`, e.g. `"exp(-x**2)"` (uses Python `math` names) | - |
| `--exact` | analytic value of the integral (computed automatically for polynomials) | - |
| `--tol` | target relative error (%) for the advisor | `1` |
| `--max-n` | largest segment count the advisor will try | `1024` |

Examples:

    python main.py --coeffs 1 2 3 --a 0 --b 2
    python main.py --expr "sin(x) + x**2" --a 0 --b 3 --n 6 --tol 0.1
    python main.py --expr "1/x" --a 1 --b 2 --exact 0.693147

## What the program prints

For each `n` you ask for, it prints:

1. The problem (function, interval, `n`)
2. Whether the trapezoid rule is applicable
3. The step size `h = (b - a) / n`
4. The nodes `x_i` and values `f(x_i)`
5. The formula with the numbers substituted in
6. The true error `Et` and relative true error (if the analytic value is known)
7. A short interpretation of the accuracy

Then the **advisor** section doubles `n` (1, 2, 4, 8, ...) until the relative
error is at or below `--tol`, and reports the smallest `n` that works.

- If the analytic value is known, the error is the **true** relative error.
- If it is not known, the error is **estimated** by comparing the result with the
  one obtained using twice as many segments.

## Expected result for the slide example

| n | Estimate | True error Et | Relative true error |
|---|---|---|---|
| 1 | 0.172800 | 1.467733 | 89.47% |
| 10 | 1.615043 | 0.025491 | 1.55% |

With the default 1% target, the advisor reports that the trapezoid rule needs
**n = 16** segments (error about 0.61%).

Note: the program uses the full-precision analytic value (1.6405333...) instead
of the rounded 1.640533 printed on the slide; the errors agree to the digits shown.

## Why a single segment fails here

`f` is a degree-5 polynomial. The trapezoid rule replaces the curve with a
straight line per segment, so it is exact only for polynomials of degree 1 or
less. Over [0, 0.8] the curve rises and falls sharply, so one segment is a poor
approximation. More segments make each straight piece fit the curve better.

## Code layout inside `main.py`

1. Core data structures (`Polynomial`, `Problem`, `Step`, `Result`)
2. `Method` base class and `@register` registry
3. `Trapezoid` method (single and composite)
4. Advisor (`advise`)
5. Report printing
6. Command-line interface

## Adding Simpson or the combined method later

Write another class in section 3 of `main.py`, subclass `Method`, implement
`check`, `estimate` and `solve`, and decorate it with `@register`. The advisor
then evaluates it automatically alongside the trapezoid rule, so the program can
tell you which method is best. Simpson 1/3 should override `n_ladder` so that it
only tries even `n`. A commented template is included in the file.

## Notes

- `--expr` evaluates the text you type with Python's `eval` (restricted to `math`
  functions). Use it only with your own input.
- Output is plain ASCII, so it works in any terminal.
- Reading of the lecturer's handwriting on the slide: "a. batas 1,2?" is treated
  as changing the upper limit to 1.2 (`--b 1.2`), and "b. n segmen" as using
  multiple segments (`--n 10`).
