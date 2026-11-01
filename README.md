# Kalkulator Integrasi Numerik / Numerical Integration Calculator

Group project for *Metoda Numerik* (Newton-Cotes formulas, Chapter 21).
One file (`main.py`), no dependencies, three team sections.

| Section | Method | Status | Owner |
|---|---|---|---|
| 2 | **Aturan Trapesium** (single + composite) | ✅ done | Bimo |
| 3 | **Aturan Simpson** (1/3 and 3/8) | 🚧 coming soon | Ihsan |
| 4 | **Metode Gabungan** (Simpson 1/3 + 3/8) | 🚧 coming soon | Kevin |

Languages: **Bahasa Indonesia** (default), **English**, **Français** — pick at startup or from the main menu.

## Cara cepat (Indonesia)

```
python main.py            # pilih bahasa di awal
python main.py --lang id  # langsung Bahasa Indonesia (en / fr juga bisa)
```
Butuh Python 3.8+. Tidak perlu install apa pun. (Opsional: `pip install matplotlib` untuk grafik gambar.)
Tekan **Enter** untuk memakai nilai bawaan `[di dalam kurung]`. Desimal boleh pakai koma (`0,8`) atau titik, dan angka boleh berupa `pi/2`.

## Quick start (English)

```
python main.py            # choose the language first
python main.py --lang en  # skip the language prompt
```
Python 3.8+, standard library only. Optional: `pip install matplotlib` for the image chart.
Press **Enter** to accept the default shown in `[brackets]`. Decimals can use a comma (`0,8`) or a dot, and numbers can be expressions like `pi/2`.

## What the Trapezoid section does

1. **Choose a function**: the slide example (21.1), a polynomial (type coefficients), or any expression such as `exp(-x^2)` or `25x - 200x^2` (`2x`, `x^2`, `sin`, `cos`, `tan`, `exp`, `log`, `sqrt`, `pi`, `e` are understood).
2. **Enter** `a`, `b`, one or more segment counts `n` (e.g. `1, 10, 20`), and a target error.
3. The program prints, for every `n`:
   - applicability check (is `f` finite on `[a, b]`?)
   - step size `h`, the nodes `f(xi)`, the formula with numbers substituted
   - **true error** `Et`, **relative true error** `et`, the slide's **estimated error** `Ea = -(b-a)^3 / (12 n^2) * f''` with the average second derivative, and an interpretation
4. A **convergence table** (n = 1, 2, 4, 6, 8, 10, 20 + your values).
5. An **advisor**: the smallest `n` that reaches your target error. If you don't know the exact integral it uses Richardson extrapolation (n vs 2n) to estimate the error.
6. A **text plot** (curve, trapezoid edge, counted area). Afterwards you can save a `.txt` report, show a matplotlib chart (saved as PNG), plot another `n`, or start over.

Slide check (Contoh 21.1, `n = 1`): `I ≈ 0.1728`, `Et = 1.467733`, `et = 89.5%`, `f'' = -60`, `Ea = 2.56` — all reproduced by the program.

Menu option **Bandingkan semua metode / Compare all methods** puts every *finished* method side by side for the same function and `n`. Unfinished methods show *coming soon*.

## Teammate guide (Sections 3 and 4)

Only edit **your own section**; Git merges stay painless. Everything you need is in the shared toolkit (Section 1):

| Helper | What it does |
|---|---|
| `ask_problem()` | asks for the function, `a`, `b` (+ exact value) → returns a `Problem` `p`; call `p(x)` to evaluate `f` safely |
| `ask_n_list("2")` | asks for one or more `n` → list of ints |
| `ask_tol()` | asks for the target error (%) |
| `title()`, `step(head, *lines)`, `say(text)` | print **and** record for the saved report (use `out()` for prompts/menus only) |
| `show_errors(p, estimate)` | prints exact value, `Et`, relative error; returns the relative error |
| `rel_err_pct(exact, est)` | relative error in % |
| `t("key")` | translated text for the current language |
| `p.exact`, `p.poly`, `p.avg_second_derivative()` | exact value (or `None`), polynomial (or `None`), mean of `f''` |

### The 3-step contract

1. **Texts**: put your strings in your section with
   ```python
   add_strings({"simp_need_even": ("n harus genap untuk Simpson 1/3.",
                                   "n must be even for Simpson 1/3.",
                                   "n doit être pair pour Simpson 1/3.")})
   ```
   Order is always *(Indonesia, English, Français)*. Don't put `{}` in a text unless it is a `{placeholder}`.
2. **Math**: implement `compute(self, p, n) -> float` returning the estimate. If `n` is not allowed, `raise ValueError(t("simp_need_even"))`. This is all the *Compare* menu needs.
3. **Screen**: implement `run(self)` (the interactive part, same style as `TrapezoidModule.run`), set your name in `owner`, set `implemented = True` and `progress = 100`.

Until `implemented = True`, your menu entry shows the **coming soon** screen with your name and progress bar, so the demo never breaks. A crash inside any module is caught and shown as a message; it does not close the program.

### Rules from the slides (to implement)

- **Simpson 1/3**: `I ≈ (b-a)/(3n) [f0 + 4(f1+f3+...) + 2(f2+f4+...) + fn]`, **n even**.
- **Simpson 3/8**: `I ≈ (3h/8) [f0 + 3f1 + 3f2 + f3]`, `n` a **multiple of 3**.
- **Combined** (slide 47): `n` even → Simpson 1/3 on all pairs; `n` odd and `n > 1` → Simpson 3/8 on the **last 3 segments**, Simpson 1/3 on the rest; `n = 1` → trapezoid.
- Check: with the slide function on `[0, 0.8]`: Simpson 1/3 `n=4` → `1.623467` (1.04%), 3/8 `n=3` → `1.519170` (7.4%), combined `n=5` → `1.645077` (-0.28%).

## Notes

- Expressions are parsed with Python's `ast` and a whitelist (numbers, `+ - * / ^ %`, `x`, and `math` functions), so arbitrary code cannot run.
- If a team prefers one file per person, move a section into its own file and `import` it. The contract above does not change.
- Reports are saved next to where you run the program (`laporan_trapesium_<date>.txt`, `grafik_trapesium_n<N>.png`).
