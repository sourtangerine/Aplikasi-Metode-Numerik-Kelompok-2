#!/usr/bin/env python3
"""
KALKULATOR INTEGRASI NUMERIK  |  Numerical Integration Calculator
Rumus Newton-Cotes - Metoda Numerik (ITS)

Bahasa / Language / Langue : Indonesia (default), English, Francais
Jalankan / Run             : python main.py            (python main.py --lang en)

FILE LAYOUT (satu file, tiga bagian tim / one file, three team sections)
  SECTION 0  translations (add_strings)                       -> shared
  SECTION 1  shared toolkit (input helpers, Problem, ...)     -> shared
  SECTION 2  TRAPESIUM / Trapezoid                            -> Bimo
  SECTION 3  SIMPSON 1/3 + 3/8                                -> Ihsan
  SECTION 4  GABUNGAN / Combined                              -> Kevin
  SECTION 5  compare + main menu                              -> shared

TEAMMATES: only edit your own section (and add your texts with add_strings
inside it). See README.md for the 3-step contract.
"""
from __future__ import annotations

import argparse
import ast
import math
import os
import re
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Optional, Sequence, Tuple

try:  # accents (French) must print correctly on Windows consoles too
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass


# ============================================================================
# SECTION 0 - TRANSLATIONS   add_strings({"key": ("indonesia", "english", "francais")})
# ============================================================================
LANGS = ["id", "en", "fr"]
LANG_NAMES = {"id": "Bahasa Indonesia", "en": "English", "fr": "Français"}
_STR: Dict[str, Dict[str, str]] = {code: {} for code in LANGS}
_lang = "id"


def add_strings(table: Dict[str, Tuple[str, str, str]]) -> None:
    for key, values in table.items():
        for code, text in zip(LANGS, values):
            _STR[code][key] = text


def set_lang(code: str) -> None:
    global _lang
    _lang = code


def t(key: str, **kw) -> str:
    """Translate a key into the current language (falls back to Indonesian)."""
    text = _STR[_lang].get(key) or _STR["id"].get(key) or key
    return text.format(**kw) if kw else text


add_strings({
    "app_title": ("KALKULATOR INTEGRASI NUMERIK", "NUMERICAL INTEGRATION CALCULATOR",
                  "CALCULATEUR D'INTÉGRATION NUMÉRIQUE"),
    "app_sub": ("Rumus Newton-Cotes | Metoda Numerik", "Newton-Cotes Formulas | Numerical Methods",
                "Formules de Newton-Cotes | Méthodes numériques"),
    "lang_prompt": ("Pilih bahasa / Choose language / Choisissez la langue",) * 3,
    "lang_set": ("Bahasa: Indonesia", "Language: English", "Langue : Français"),
    "menu_title": ("MENU UTAMA", "MAIN MENU", "MENU PRINCIPAL"),
    "menu_trap": ("Aturan Trapesium", "Trapezoidal Rule", "Méthode des trapèzes"),
    "menu_simp": ("Aturan Simpson (1/3 dan 3/8)", "Simpson's Rules (1/3 and 3/8)",
                  "Règles de Simpson (1/3 et 3/8)"),
    "menu_comb": ("Metode Gabungan (Simpson 1/3 + 3/8)", "Combined Method (Simpson 1/3 + 3/8)",
                  "Méthode combinée (Simpson 1/3 + 3/8)"),
    "menu_cmp": ("Bandingkan semua metode", "Compare all methods", "Comparer toutes les méthodes"),
    "menu_lang": ("Ganti bahasa", "Change language", "Changer de langue"),
    "menu_exit": ("Keluar", "Exit", "Quitter"),
    "menu_choice": ("Pilih menu", "Choose an option", "Choisissez une option"),
    "bad_choice": ("Pilihan tidak valid.", "Invalid choice.", "Choix invalide."),
    "bye": ("Terima kasih, sampai jumpa!", "Thank you, goodbye!", "Merci, à bientôt !"),
    "press_enter": ("Tekan Enter untuk kembali...", "Press Enter to go back...",
                    "Appuyez sur Entrée pour revenir..."),
    "soon_tag": ("[segera hadir]", "[coming soon]", "[bientôt disponible]"),
    "soon_title": ("SEGERA HADIR", "COMING SOON", "BIENTÔT DISPONIBLE"),
    "soon_body": ("Bagian ini sedang dikerjakan oleh anggota tim. Nantikan ya!",
                  "This section is being built by a teammate. Stay tuned!",
                  "Cette section est en cours de développement par un coéquipier. Restez connecté !"),
    "soon_owner": ("Penanggung jawab: {owner}", "Owner: {owner}", "Responsable : {owner}"),
    "soon_progress": ("Progres", "Progress", "Progression"),
    "module_error": ("Terjadi kesalahan di modul '{name}': {err}",
                     "An error occurred in module '{name}': {err}",
                     "Une erreur est survenue dans le module « {name} » : {err}"),
    "invalid_number": ("Masukan tidak valid, coba lagi (contoh: 0,8 atau pi/2).",
                       "Invalid input, try again (e.g. 0.8 or pi/2).",
                       "Entrée invalide, réessayez (ex. : 0,8 ou pi/2)."),
    "int_range": ("Masukkan bilangan bulat antara {lo} dan {hi}.",
                  "Enter whole numbers between {lo} and {hi}.",
                  "Saisissez des entiers entre {lo} et {hi}."),
    # --- function / interval input (shared by every method) ---
    "fn_source": ("Pilih sumber fungsi:", "Choose the function source:",
                  "Choisissez la source de la fonction :"),
    "fn_opt1": ("Contoh slide 21.1: f(x) = 0.2 + 25x - 200x^2 + 675x^3 - 900x^4 + 400x^5",
                "Slide example 21.1: f(x) = 0.2 + 25x - 200x^2 + 675x^3 - 900x^4 + 400x^5",
                "Exemple du cours 21.1 : f(x) = 0.2 + 25x - 200x^2 + 675x^3 - 900x^4 + 400x^5"),
    "fn_opt2": ("Polinomial (masukkan koefisien)", "Polynomial (enter coefficients)",
                "Polynôme (saisir les coefficients)"),
    "fn_opt3": ("Ekspresi bebas f(x), mis. sin(x) + x^2", "Free expression f(x), e.g. sin(x) + x^2",
                "Expression libre f(x), ex. sin(x) + x^2"),
    "ex_coeffs": ("contoh: 0.2 25 -200 675 -900 400   (= 0.2 + 25x - 200x^2 + ...)",
                  "example: 0.2 25 -200 675 -900 400   (= 0.2 + 25x - 200x^2 + ...)",
                  "exemple : 0.2 25 -200 675 -900 400   (= 0.2 + 25x - 200x^2 + ...)"),
    "ask_coeffs": ("Koefisien dari pangkat terendah (c0 c1 c2 ...), pisahkan dengan spasi",
                   "Coefficients from the lowest power (c0 c1 c2 ...), space-separated",
                   "Coefficients depuis la puissance la plus basse (c0 c1 c2 ...), séparés par des espaces"),
    "bad_coeffs": ("Koefisien tidak valid.", "Invalid coefficients.", "Coefficients invalides."),
    "expr_help": ("pakai x; fungsi: sin cos tan exp log sqrt; boleh 2x dan x^2; konstanta: pi, e",
                  "use x; functions: sin cos tan exp log sqrt; 2x and x^2 allowed; constants: pi, e",
                  "utilisez x ; fonctions : sin cos tan exp log sqrt ; 2x et x^2 acceptés ; constantes : pi, e"),
    "ask_expr": ("Tulis f(x)", "Type f(x)", "Saisissez f(x)"),
    "bad_expr": ("Ekspresi tidak valid: {err}", "Invalid expression: {err}",
                 "Expression invalide : {err}"),
    "ask_a": ("Batas bawah a", "Lower limit a", "Borne inférieure a"),
    "ask_b": ("Batas atas b", "Upper limit b", "Borne supérieure b"),
    "err_ab": ("Syarat: a harus lebih kecil dari b.", "Requirement: a must be smaller than b.",
               "Condition : a doit être inférieur à b."),
    "ask_n": ("Jumlah segmen n (boleh beberapa, pisahkan koma, mis. 1, 10, 20)",
              "Number of segments n (several allowed, comma-separated, e.g. 1, 10, 20)",
              "Nombre de segments n (plusieurs possibles, séparés par des virgules, ex. 1, 10, 20)"),
    "ask_exact": ("Nilai integral eksak (kosongkan jika tidak tahu)",
                  "Exact integral value (leave blank if unknown)",
                  "Valeur exacte de l'intégrale (laisser vide si inconnue)"),
    "exact_auto": ("Nilai eksak dihitung otomatis dari antiturunan: {v}",
                   "Exact value computed automatically from the antiderivative: {v}",
                   "Valeur exacte calculée automatiquement à partir de la primitive : {v}"),
    "ask_tol": ("Target galat relatif untuk penasihat (%)", "Target relative error for the advisor (%)",
                "Erreur relative cible pour le conseiller (%)"),
    "tol_positive": ("Masukkan angka positif.", "Enter a positive number.",
                     "Saisissez un nombre positif."),
    # --- error labels (shared) ---
    "lbl_exact": ("Nilai eksak (analitik)", "Exact (analytic) value", "Valeur exacte (analytique)"),
    "lbl_et": ("Galat sejati Et", "True error Et", "Erreur vraie Et"),
    "lbl_rel": ("Galat relatif sejati et", "True relative error et", "Erreur relative vraie et"),
    "interp_none": ("Nilai eksak tidak diketahui, jadi galat sejati tidak bisa dihitung.",
                    "The exact value is unknown, so the true error cannot be computed.",
                    "La valeur exacte est inconnue, l'erreur vraie ne peut donc pas être calculée."),
    "result": ("HASIL", "RESULT", "RÉSULTAT"),
})


# ============================================================================
# SECTION 1 - SHARED TOOLKIT  (everybody uses it - please keep signatures stable)
# ============================================================================
MAX_N = 1_000_000
LOG: List[str] = []          # everything printed with say() ends up in the saved report
out = print                  # print only (menus, prompts)


def say(text: str = "") -> None:
    """Print AND remember for the .txt report."""
    print(text)
    LOG.append(text)


def hr(char: str = "=", width: int = 72) -> None:
    say(char * width)


def title(text: str) -> None:
    say()
    hr()
    say("  " + text)
    hr()


def step(head: str, *lines: str) -> None:
    say()
    say(head)
    for line in lines:
        say("    " + line)


def fmt(x: float) -> str:
    return f"{x:.6g}"


def ask(prompt: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default not in (None, "") else ""
    raw = input(f"{prompt}{suffix}: ").strip()
    return raw if raw else (default or "")


# ---- safe math-expression parser (no eval of arbitrary code) ----------------
_NAMES = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
_NAMES.update({"ln": math.log, "abs": abs})
_OK_NODES = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name, ast.Load, ast.Constant,
             ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.USub, ast.UAdd)


def compile_expr(expr: str, with_x: bool = True) -> Callable[[float], float]:
    """'25x - 200x^2 + sin(pi*x)' -> python function of x (validated with ast)."""
    expr = expr.strip().replace("^", "**")
    # implicit multiplication: 25x -> 25*x, 3(x+1) -> 3*(x+1), 2pi -> 2*pi (not 2e3, not log10())
    expr = re.sub(r"(?<![A-Za-z_\d.])(\d+(?:\.\d+)?)(?![eE][+-]?\d)\s*(?=[A-Za-z_(])", r"\1*", expr)
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _OK_NODES):
            raise ValueError(type(node).__name__)
        if isinstance(node, ast.Name) and node.id not in _NAMES and not (with_x and node.id == "x"):
            raise ValueError(node.id)
        if isinstance(node, ast.Call) and not (isinstance(node.func, ast.Name) and node.func.id in _NAMES):
            raise ValueError("call")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            raise ValueError("constant")
    code = compile(tree, "<f>", "eval")
    env = {"__builtins__": {}, **_NAMES}

    def f(x: float) -> float:
        env["x"] = x
        return eval(code, env)  # noqa: S307  (tree already whitelisted)
    return f


def num(text: str) -> float:
    """Parse '0,8', '0.8', 'pi/2', '2*pi' ..."""
    text = text.strip()
    if "," in text and "(" not in text:
        text = text.replace(",", ".")
    value = float(compile_expr(text, with_x=False)(0.0))
    if not math.isfinite(value):
        raise ValueError(text)
    return value


def ask_float(key: str, default: Optional[str] = None) -> float:
    while True:
        try:
            return num(ask(t(key), default))
        except Exception:  # noqa: BLE001
            out(t("invalid_number"))


def ask_int(key: str, default: str, lo: int = 1, hi: int = MAX_N) -> int:
    while True:
        try:
            v = int(ask(t(key), default))
            if lo <= v <= hi:
                return v
        except ValueError:
            pass
        out(t("int_range", lo=lo, hi=hi))


def ask_n_list(default: str = "1") -> List[int]:
    while True:
        raw = ask(t("ask_n"), default)
        try:
            ns = [int(x) for x in re.split(r"[,\s;]+", raw) if x]
            if ns and all(1 <= n <= MAX_N for n in ns):
                return list(dict.fromkeys(ns))      # unique, keeps order
        except ValueError:
            pass
        out(t("int_range", lo=1, hi=MAX_N))


def ask_tol() -> float:
    while True:
        v = ask_float("ask_tol", "1")
        if v > 0:
            return v
        out(t("tol_positive"))


# ---- function model ---------------------------------------------------------
class FunctionError(Exception):
    def __init__(self, x: float, msg: object):
        super().__init__(msg)
        self.x, self.msg = x, msg


class Polynomial:
    """coeffs[i] = coefficient of x**i."""

    def __init__(self, coeffs: Sequence[float]):
        self.coeffs = [float(c) for c in coeffs]
        while len(self.coeffs) > 1 and self.coeffs[-1] == 0:
            self.coeffs.pop()

    def __call__(self, x: float) -> float:
        r = 0.0
        for c in reversed(self.coeffs):
            r = r * x + c
        return r

    @property
    def degree(self) -> int:
        return len(self.coeffs) - 1

    def antiderivative(self) -> "Polynomial":
        return Polynomial([0.0] + [c / (i + 1) for i, c in enumerate(self.coeffs)])

    def derivative(self) -> "Polynomial":
        return Polynomial([i * c for i, c in enumerate(self.coeffs)][1:] or [0.0])

    def __str__(self) -> str:
        s = ""
        for i, c in enumerate(self.coeffs):
            if c == 0:
                continue
            mag = f"{abs(c):g}"
            term = mag if i == 0 else ("" if abs(c) == 1 else mag) + "x" + (f"^{i}" if i > 1 else "")
            s += (("-" if c < 0 else "") + term) if not s else (" - " if c < 0 else " + ") + term
        return s or "0"


@dataclass
class Problem:
    f: Callable[[float], float]
    label: str
    a: float
    b: float
    exact: Optional[float] = None
    poly: Optional[Polynomial] = None

    def __call__(self, x: float) -> float:
        """Safe f(x): raises FunctionError instead of crashing."""
        try:
            v = float(self.f(x))
        except (ArithmeticError, ValueError, TypeError) as exc:
            raise FunctionError(x, exc)
        if not math.isfinite(v):
            raise FunctionError(x, "inf/nan")
        return v

    def avg_second_derivative(self) -> Optional[float]:
        """mean of f'' on [a,b] = (f'(b) - f'(a)) / (b - a)   (slide: f''-bar = -60)."""
        try:
            if self.poly is not None:
                d = self.poly.derivative()
                return (d(self.b) - d(self.a)) / (self.b - self.a)
            h = (self.b - self.a) * 1e-4                   # one-sided stencils stay inside [a, b]
            fa = (-3 * self(self.a) + 4 * self(self.a + h) - self(self.a + 2 * h)) / (2 * h)
            fb = (3 * self(self.b) - 4 * self(self.b - h) + self(self.b - 2 * h)) / (2 * h)
            return (fb - fa) / (self.b - self.a)
        except FunctionError:
            return None


PRESET_COEFFS = [0.2, 25, -200, 675, -900, 400]


def ask_problem() -> Problem:
    """Interactive: function + limits (+ exact value). Reuse this in every method."""
    out()
    out(t("fn_source"))
    for i in (1, 2, 3):
        out(f"  {i}) {t('fn_opt' + str(i))}")
    while True:
        choice = ask(t("menu_choice"), "1")
        if choice in ("1", "2", "3"):
            break
        out(t("bad_choice"))
    poly: Optional[Polynomial] = None
    f: Callable[[float], float] = lambda x: 0.0     # noqa: E731
    expr = ""
    da, db = "0", "1"
    if choice == "1":
        poly, db = Polynomial(PRESET_COEFFS), "0.8"
    elif choice == "2":
        out(t("ex_coeffs"))
        while True:
            try:
                coeffs = [num(tok) for tok in ask(t("ask_coeffs")).split()]
                if not coeffs:
                    raise ValueError
                poly = Polynomial(coeffs)
                break
            except Exception:  # noqa: BLE001
                out(t("bad_coeffs"))
    else:
        out(t("expr_help"))
        while True:
            expr = ask(t("ask_expr"))
            try:
                f = compile_expr(expr)
                break
            except Exception as exc:  # noqa: BLE001
                out(t("bad_expr", err=exc))
    a = ask_float("ask_a", da)
    while True:
        b = ask_float("ask_b", db)
        if a < b:
            break
        out(t("err_ab"))
    exact: Optional[float] = None
    if poly is not None:
        F = poly.antiderivative()
        exact = F(b) - F(a)
        out(t("exact_auto", v=f"{exact:.7f}"))
        return Problem(poly, f"f(x) = {poly}", a, b, exact, poly)
    while True:
        raw = ask(t("ask_exact"), "")
        if not raw:
            break
        try:
            exact = num(raw)
            break
        except Exception:  # noqa: BLE001
            out(t("invalid_number"))
    return Problem(f, f"f(x) = {expr}", a, b, exact, None)


def show_errors(p: Problem, est: float) -> Optional[float]:
    """Prints exact value, Et and relative error. Returns signed relative error (%)."""
    if p.exact is None:
        say("    " + t("interp_none"))
        return None
    et = p.exact - est
    rel = et / (p.exact if p.exact != 0 else 1.0) * 100
    say(f"    {t('lbl_exact')} I = {p.exact:.7f}")
    say(f"    {t('lbl_et')} = {p.exact:.7f} - {est:.6f} = {et:.6f}")
    say(f"    {t('lbl_rel')} = Et / I x 100% = {rel:.4f}%")
    return rel


def rel_err_pct(exact: float, est: float) -> float:
    return abs(exact - est) / (abs(exact) if exact != 0 else 1.0) * 100


class MethodModule:
    """Contract for every method section. Teammates: subclass, set the flags,
    implement compute() and run()."""
    key = ""
    title_key = ""          # translation key of the menu name
    owner = "-"             # who is responsible (shown on the coming-soon screen)
    implemented = False     # True  -> appears as a real method everywhere
    progress = 0            # 0..100 (shown on the coming-soon screen)

    def compute(self, p: Problem, n: int) -> float:
        """Return the integral estimate for n segments. Raise ValueError(msg) if n is
        not allowed (e.g. odd n for Simpson 1/3)."""
        raise NotImplementedError

    def run(self) -> None:
        """Interactive screen of the method (menu entry)."""
        coming_soon(self)
        ask(t("press_enter"))


def coming_soon(m: MethodModule) -> None:
    w = 62

    def line(s: str = "") -> None:
        out("| " + s.center(w - 4) + " |")

    out()
    out("+" + "-" * (w - 2) + "+")
    line()
    line(t("soon_title"))
    for part in textwrap.wrap(t(m.title_key), w - 8):
        line(part)
    line()
    for part in textwrap.wrap(t("soon_body"), w - 8):
        line(part)
    line()
    line(t("soon_owner", owner=m.owner))
    filled = int(20 * m.progress / 100)
    line(f"{t('soon_progress')}: [{'#' * filled}{'-' * (20 - filled)}] {m.progress}%")
    line()
    out("+" + "-" * (w - 2) + "+")


# ============================================================================
# SECTION 2 - TRAPESIUM / TRAPEZOID   (DONE)          owner: <nama kamu>
# ============================================================================
add_strings({
    "trap_title": ("ATURAN TRAPESIUM", "TRAPEZOIDAL RULE", "MÉTHODE DES TRAPÈZES"),
    "trap_intro": ("Menaksir integral dengan garis lurus (polinom orde 1) pada tiap segmen.",
                   "Approximates the integral with straight lines (order-1 polynomial) on each segment.",
                   "Approche l'intégrale par des segments de droite (polynôme d'ordre 1) sur chaque sous-intervalle."),
    "run_single": ("TRAPESIUM SATU SEGMEN", "SINGLE-SEGMENT TRAPEZOID", "TRAPÈZE À UN SEGMENT"),
    "run_multi": ("TRAPESIUM MAJEMUK (n = {n} segmen)", "COMPOSITE TRAPEZOID (n = {n} segments)",
                  "TRAPÈZES COMPOSÉS (n = {n} segments)"),
    "s_problem": ("Langkah 1 - Soal", "Step 1 - Problem", "Étape 1 - Problème"),
    "sum_int": ("Selang [a, b]", "Interval [a, b]", "Intervalle [a, b]"),
    "sum_n": ("Jumlah segmen n", "Number of segments n", "Nombre de segments n"),
    "sum_exact": ("Nilai eksak", "Exact value", "Valeur exacte"),
    "sum_unknown": ("tidak diketahui", "unknown", "inconnue"),
    "sum_tol": ("Target galat", "Error target", "Erreur cible"),
    "s_applic": ("Langkah 2 - Apakah metode ini berlaku?", "Step 2 - Is the method applicable?",
                 "Étape 2 - La méthode est-elle applicable ?"),
    "applic_yes": ("YA: f(x) terdefinisi dan terhingga di seluruh [a, b], aturan dapat dipakai.",
                   "YES: f(x) is defined and finite on all of [a, b]; the rule can be used.",
                   "OUI : f(x) est définie et finie sur tout [a, b] ; la règle est applicable."),
    "applic_no": ("TIDAK: f(x) tidak dapat dihitung di x = {x} ({err}).",
                  "NO: f(x) cannot be evaluated at x = {x} ({err}).",
                  "NON : f(x) ne peut pas être évaluée en x = {x} ({err})."),
    "applic_linear": ("f linear, sehingga trapesium EKSAK.", "f is linear, so the trapezoid rule is EXACT.",
                      "f est linéaire, la règle des trapèzes est donc EXACTE."),
    "applic_poly": ("f polinomial derajat {d}; trapesium hanya eksak untuk derajat <= 1, jadi ada galat pemotongan.",
                    "f is a degree-{d} polynomial; the rule is exact only for degree <= 1, so truncation error is expected.",
                    "f est un polynôme de degré {d} ; la règle n'est exacte que pour le degré <= 1, il y aura une erreur de troncature."),
    "s_h": ("Langkah 3 - Lebar segmen", "Step 3 - Segment width", "Étape 3 - Largeur d'un segment"),
    "s_nodes": ("Langkah 4 - Hitung f di tiap titik", "Step 4 - Evaluate f at each node",
                "Étape 4 - Évaluer f en chaque nœud"),
    "more_nodes": ("... ({k} titik lainnya) ...", "... ({k} more nodes) ...", "... ({k} autres nœuds) ..."),
    "s_formula": ("Langkah 5 - Terapkan rumus", "Step 5 - Apply the formula", "Étape 5 - Appliquer la formule"),
    "sum_interior": ("Jumlah f di titik dalam = {s}", "Sum of interior f values = {s}",
                     "Somme des f intérieures = {s}"),
    "s_errors": ("Langkah 6 - Galat", "Step 6 - Errors", "Étape 6 - Erreurs"),
    "lbl_f2": ("Rata-rata turunan kedua f''", "Average second derivative f''",
               "Moyenne de la dérivée seconde f''"),
    "lbl_ea": ("Estimasi galat Ea", "Estimated error Ea", "Erreur estimée Ea"),
    "ea_note": ("(Ea hanya perkiraan kasar, bukan galat sebenarnya.)",
                "(Ea is only a rough estimate, not the real error.)",
                "(Ea n'est qu'une estimation grossière, pas l'erreur réelle.)"),
    "s_interp": ("Langkah 7 - Interpretasi", "Step 7 - Interpretation", "Étape 7 - Interprétation"),
    "interp_good": ("Akurasi baik (< 1%).", "Good accuracy (< 1%).", "Bonne précision (< 1 %)."),
    "interp_mid": ("Akurasi sedang; perbesar n untuk hasil lebih baik.",
                   "Moderate accuracy; increase n for a better result.",
                   "Précision moyenne ; augmentez n pour un meilleur résultat."),
    "interp_bad": ("Akurasi buruk: garis lurus tidak bisa mengikuti kelengkungan fungsi pada segmen selebar ini. Perbesar n.",
                   "Poor accuracy: straight lines cannot follow the curvature over segments this wide. Increase n.",
                   "Mauvaise précision : des droites ne suivent pas la courbure sur des segments aussi larges. Augmentez n."),
    "conv_title": ("TABEL KONVERGENSI", "CONVERGENCE TABLE", "TABLEAU DE CONVERGENCE"),
    "conv_chg": ("perub.%", "change%", "var.%"),
    "conv_note": ("'<' = n yang kamu minta. Galat turun sekitar 4x setiap n digandakan (orde O(h^2)).",
                  "'<' = the n you asked for. The error drops about 4x each time n doubles (order O(h^2)).",
                  "'<' = le n demandé. L'erreur est divisée par ~4 chaque fois que n double (ordre O(h^2))."),
    "adv_title": ("PENASIHAT: APAKAH METODE INI COCOK?", "ADVISOR: DOES THIS METHOD WORK?",
                  "CONSEILLER : CETTE MÉTHODE CONVIENT-ELLE ?"),
    "adv_target": ("Target: galat relatif <= {tol}% ({basis})", "Target: relative error <= {tol}% ({basis})",
                   "Cible : erreur relative <= {tol} % ({basis})"),
    "basis_true": ("galat sejati", "true error", "erreur vraie"),
    "basis_est": ("galat estimasi: ekstrapolasi Richardson n vs 2n",
                  "estimated error: Richardson extrapolation, n vs 2n",
                  "erreur estimée : extrapolation de Richardson, n vs 2n"),
    "adv_n1": ("Satu segmen (n = 1): galat = {e}%", "Single segment (n = 1): error = {e}%",
               "Un seul segment (n = 1) : erreur = {e} %"),
    "adv_ok": ("COCOK: target tercapai dengan n minimum = {n} segmen (galat = {e}%, I = {I}).",
               "WORKS: target reached with a minimum of n = {n} segments (error = {e}%, I = {I}).",
               "CONVIENT : cible atteinte avec un minimum de n = {n} segments (erreur = {e} %, I = {I})."),
    "adv_fail": ("BELUM COCOK: target tidak tercapai sampai n = {n} (galat terakhir = {e}%).",
                 "NOT ENOUGH: target not reached up to n = {n} (last error = {e}%).",
                 "INSUFFISANT : cible non atteinte jusqu'à n = {n} (dernière erreur = {e} %)."),
    "adv_tip": ("Tip: coba metode lain lewat menu 'Bandingkan semua metode'.",
                "Tip: try the other methods via 'Compare all methods'.",
                "Astuce : essayez les autres méthodes via « Comparer toutes les méthodes »."),
    "plot_title": ("GRAFIK TEKS (n = {n})", "TEXT PLOT (n = {n})", "GRAPHIQUE TEXTE (n = {n})"),
    "plot_legend": ("* kurva f(x)   # sisi atas trapesium   : daerah yang dihitung",
                    "* curve f(x)   # trapezoid top edge   : area counted",
                    "* courbe f(x)   # côté supérieur du trapèze   : aire comptée"),
    "post_title": ("APA SELANJUTNYA?", "WHAT NEXT?", "ET ENSUITE ?"),
    "post_save": ("Simpan laporan ke file .txt", "Save the report to a .txt file",
                  "Enregistrer le rapport dans un fichier .txt"),
    "post_mpl": ("Tampilkan grafik (matplotlib)", "Show a chart (matplotlib)",
                 "Afficher un graphique (matplotlib)"),
    "post_ascii": ("Grafik teks untuk n lain", "Text plot for another n", "Graphique texte pour un autre n"),
    "post_again": ("Hitung lagi dengan data baru", "Calculate again with new data",
                   "Recalculer avec de nouvelles données"),
    "post_back": ("Kembali ke menu utama", "Back to the main menu", "Retour au menu principal"),
    "saved": ("Laporan disimpan: {path}", "Report saved: {path}", "Rapport enregistré : {path}"),
    "saved_chart": ("Grafik disimpan: {path}", "Chart saved: {path}", "Graphique enregistré : {path}"),
    "no_mpl": ("matplotlib belum terpasang. Jalankan: pip install matplotlib",
               "matplotlib is not installed. Run: pip install matplotlib",
               "matplotlib n'est pas installé. Exécutez : pip install matplotlib"),
    "ask_plot_n": ("Gambar untuk n berapa", "Plot for which n", "Tracer pour quel n"),
})


def ascii_plot(p: Problem, n: int, width: int = 64, height: int = 16) -> str:
    """Text chart: curve (*), trapezoid top edge (#), counted area (:)."""
    cols = [p.a + (p.b - p.a) * c / (width - 1) for c in range(width)]
    curve = [p(x) for x in cols]
    nodes = [p.a + (p.b - p.a) * i / n for i in range(n + 1)]
    fn = [p(x) for x in nodes]

    def edge_at(x: float) -> float:
        i = min(int((x - p.a) / (p.b - p.a) * n), n - 1)
        return fn[i] + (fn[i + 1] - fn[i]) * (x - nodes[i]) / (nodes[i + 1] - nodes[i])

    edge = [edge_at(x) for x in cols]
    lo, hi = min(0.0, min(curve), min(edge)), max(0.0, max(curve), max(edge))
    if hi == lo:
        hi = lo + 1.0

    def row(v: float) -> int:
        return max(0, min(height - 1, round((hi - v) / (hi - lo) * (height - 1))))

    z = row(0.0)
    grid = [[" "] * width for _ in range(height)]
    for c in range(width):
        grid[z][c] = "-"
        r_e = row(edge[c])
        for r in (range(r_e, z) if r_e < z else range(z + 1, r_e + 1)):
            grid[r][c] = ":"
    if n <= 20:                                           # vertical sides of the trapezoids
        for i in range(n + 1):
            c = round(i / n * (width - 1))
            for r in range(min(z, row(fn[i])), max(z, row(fn[i])) + 1):
                grid[r][c] = "|"
    for c in range(width):
        grid[row(edge[c])][c] = "#"
        grid[row(curve[c])][c] = "*"
    lines = []
    for r in range(height):
        label = f"{hi:>9.3f}" if r == 0 else (f"{lo:>9.3f}" if r == height - 1 else " " * 9)
        lines.append(f"{label} |{''.join(grid[r])}")
    lines.append(" " * 10 + "+" + "-" * width)
    lines.append(" " * 11 + f"{p.a:g}".ljust(width - len(f"{p.b:g}")) + f"{p.b:g}")
    lines.append(" " * 11 + t("plot_legend"))
    return "\n".join(lines)


class TrapezoidModule(MethodModule):
    key = "trapezoid"
    title_key = "menu_trap"
    owner = "Kamu / You"
    implemented = True
    progress = 100

    # ---- numerics -----------------------------------------------------------
    @staticmethod
    def nodes(p: Problem, n: int) -> Tuple[float, List[float], List[float]]:
        h = (p.b - p.a) / n
        xs = [p.a + i * h for i in range(n + 1)]
        xs[-1] = p.b
        return h, xs, [p(x) for x in xs]

    def compute(self, p: Problem, n: int) -> float:
        if not 1 <= n <= MAX_N:
            raise ValueError(t("int_range", lo=1, hi=MAX_N))
        h, _, fs = self.nodes(p, n)
        return h / 2 * (fs[0] + 2 * math.fsum(fs[1:-1]) + fs[-1])

    def applicable(self, p: Problem) -> Tuple[bool, str]:
        try:
            for i in range(41):
                p(p.a + (p.b - p.a) * i / 40)
        except FunctionError as exc:
            return False, t("applic_no", x=fmt(exc.x), err=exc.msg)
        msg = t("applic_yes")
        if p.poly is not None:
            msg += " " + (t("applic_linear") if p.poly.degree <= 1 else t("applic_poly", d=p.poly.degree))
        return True, msg

    # ---- report blocks ------------------------------------------------------
    def show(self, p: Problem, n: int) -> None:
        h, xs, fs = self.nodes(p, n)
        est = self.compute(p, n)
        title(t("run_single") if n == 1 else t("run_multi", n=n))
        step(t("s_h"), "h = (b - a) / n", f"h = ({fmt(p.b)} - {fmt(p.a)}) / {n} = {fmt(h)}")
        rows = [f"x{i} = {x:.6g}   f(x{i}) = {fx:.6f}" for i, (x, fx) in enumerate(zip(xs, fs))]
        if len(rows) > 12:
            rows = rows[:4] + [t("more_nodes", k=len(rows) - 6)] + rows[-2:]
        step(t("s_nodes"), *rows)
        if n == 1:
            step(t("s_formula"), "I ~ (b - a) * [f(a) + f(b)] / 2",
                 f"I ~ {fmt(p.b - p.a)} * ({fs[0]:.6f} + {fs[-1]:.6f}) / 2", f"I ~ {est:.6f}")
        else:
            inner = math.fsum(fs[1:-1])
            step(t("s_formula"), "I ~ (h/2) * [ f(x0) + 2*(f(x1) + ... + f(x(n-1))) + f(xn) ]",
                 t("sum_interior", s=f"{inner:.6f}"),
                 f"I ~ ({fmt(h)}/2) * [ {fs[0]:.6f} + 2*{inner:.6f} + {fs[-1]:.6f} ]", f"I ~ {est:.6f}")
        say()
        say(t("s_errors"))
        rel = show_errors(p, est)
        f2 = p.avg_second_derivative()
        if f2 is not None:
            ea = -(p.b - p.a) ** 3 / (12 * n ** 2) * f2
            say(f"    {t('lbl_f2')} = {f2:.6g}")
            say(f"    {t('lbl_ea')} = -(b-a)^3 / (12 n^2) * f'' = {ea:.6g}")
            say(f"    {t('ea_note')}")
        if rel is not None:
            r = abs(rel)
            step(t("s_interp"), t("interp_good") if r < 1 else t("interp_mid") if r < 10 else t("interp_bad"))
        say()
        say(f">>> {t('result')}: I ~ {est:.6f}")

    def convergence(self, p: Problem, ns: List[int]) -> None:
        title(t("conv_title"))
        if p.exact is not None:
            say(f"{'n':>8} {'h':>12} {'I':>14} {'Et':>12} {'|et| %':>10}")
        else:
            say(f"{'n':>8} {'h':>12} {'I':>14} {t('conv_chg'):>10}")
        for n in sorted(set([1, 2, 4, 6, 8, 10, 20]) | set(ns)):
            est = self.compute(p, n)
            h = (p.b - p.a) / n
            mark = " <" if n in ns else ""
            if p.exact is not None:
                say(f"{n:>8} {h:>12.6g} {est:>14.6f} {p.exact - est:>12.6f} {rel_err_pct(p.exact, est):>10.4f}{mark}")
            else:
                finer = self.compute(p, 2 * n)
                say(f"{n:>8} {h:>12.6g} {est:>14.6f} {rel_err_pct(finer, est):>10.4f}{mark}")
        say(t("conv_note"))

    def advise(self, p: Problem, tol: float) -> None:
        """Smallest n that reaches the target error (doubling, then bisection)."""
        title(t("adv_title"))
        say(t("adv_target", tol=f"{tol:g}", basis=t("basis_true") if p.exact is not None else t("basis_est")))
        cache: Dict[int, Tuple[float, float]] = {}

        def err(n: int) -> Tuple[float, float]:
            if n not in cache:
                est = self.compute(p, n)
                if p.exact is not None:
                    ref = p.exact
                else:   # Richardson: error ~ h^2, so (4*I(2n) - I(n)) / 3 is a better reference
                    ref = (4 * self.compute(p, 2 * n) - est) / 3
                cache[n] = (rel_err_pct(ref, est), est)
            return cache[n]

        say(t("adv_n1", e=f"{err(1)[0]:.4f}"))
        lo, hi, n, limit = 0, None, 1, 2 ** 16
        while n <= limit:
            if err(n)[0] <= tol:
                hi = n
                break
            lo, n = n, n * 2
        if hi is None:
            say(t("adv_fail", n=limit, e=f"{err(limit)[0]:.4f}"))
        else:
            while lo + 1 < hi:
                mid = (lo + hi) // 2
                lo, hi = (lo, mid) if err(mid)[0] <= tol else (mid, hi)
            say(t("adv_ok", n=hi, e=f"{err(hi)[0]:.4f}", I=f"{err(hi)[1]:.6f}"))
        if any(m.implemented for m in MODULES if m is not self):
            say(t("adv_tip"))

    # ---- extras -------------------------------------------------------------
    def mpl_plot(self, p: Problem, n: int) -> None:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            out(t("no_mpl"))
            return
        _, xs, fs = self.nodes(p, n)
        grid = [p.a + (p.b - p.a) * i / 400 for i in range(401)]
        plt.figure(figsize=(8, 5))
        plt.plot(grid, [p(x) for x in grid], "b-", label="f(x)")
        plt.fill_between(xs, fs, alpha=0.3, color="orange", label=t("trap_title"))
        if n <= 100:
            plt.vlines(xs, 0, fs, colors="k", linewidth=0.6)
        plt.plot(xs, fs, "ro-", markersize=3)
        plt.title(f"{t('trap_title')}  n = {n}   I ~ {self.compute(p, n):.6f}")
        plt.grid(alpha=0.3)
        plt.legend()
        path = f"grafik_trapesium_n{n}.png"
        plt.savefig(path, dpi=150)
        out(t("saved_chart", path=os.path.abspath(path)))
        try:
            plt.show()
        except Exception:  # noqa: BLE001
            pass

    @staticmethod
    def save_report() -> None:
        path = f"laporan_trapesium_{datetime.now():%Y%m%d_%H%M%S}.txt"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(LOG) + "\n")
        out(t("saved", path=os.path.abspath(path)))

    def post_menu(self, p: Problem, ns: List[int], computed: bool) -> str:
        while True:
            out()
            out(t("post_title"))
            options = [("1", "post_save"), ("2", "post_mpl"), ("3", "post_ascii")] if computed else []
            options += [("4", "post_again"), ("0", "post_back")]
            for key, label in options:
                out(f"  {key}) {t(label)}")
            choice = ask(t("menu_choice"), "0")
            if choice not in dict(options):
                out(t("bad_choice"))
            elif choice == "1":
                self.save_report()
            elif choice in ("2", "3"):
                n = ask_int("ask_plot_n", str(ns[0]), 1, 100_000)
                if choice == "2":
                    self.mpl_plot(p, n)
                else:
                    out(); out(t("plot_title", n=n)); out(ascii_plot(p, n))
            elif choice == "4":
                return "again"
            else:
                return "back"

    # ---- interactive screen -------------------------------------------------
    def run(self) -> None:
        while True:
            LOG.clear()
            title(t("trap_title"))
            say(t("trap_intro"))
            p = ask_problem()
            ns = ask_n_list("1")
            tol = ask_tol()
            step(t("s_problem"), p.label, f"{t('sum_int')} = [{fmt(p.a)}, {fmt(p.b)}]",
                 f"{t('sum_n')} = {', '.join(map(str, ns))}",
                 f"{t('sum_exact')} = {p.exact:.7f}" if p.exact is not None
                 else f"{t('sum_exact')} = {t('sum_unknown')}", f"{t('sum_tol')} = {tol:g}%")
            ok, msg = self.applicable(p)
            step(t("s_applic"), msg)
            if ok:
                try:
                    for n in ns:
                        self.show(p, n)
                    self.convergence(p, ns)
                    self.advise(p, tol)
                    say()
                    say(t("plot_title", n=ns[0]))
                    say(ascii_plot(p, ns[0]))
                except FunctionError as exc:
                    ok = False
                    say(t("applic_no", x=fmt(exc.x), err=exc.msg))
            if self.post_menu(p, ns, ok) == "back":
                return


# ============================================================================
# SECTION 3 - SIMPSON 1/3 + 3/8                       TEAMMATE A  (belum dikerjakan)
# ============================================================================
add_strings({
    # TEAMMATE A: add your own texts here, e.g.
    # "simp_need_even": ("n harus genap untuk Simpson 1/3.", "n must be even for Simpson 1/3.",
    #                    "n doit être pair pour Simpson 1/3."),
})


class SimpsonModule(MethodModule):
    key = "simpson"
    title_key = "menu_simp"
    owner = "Anggota Tim A"     # <- TEAMMATE A: write your name
    implemented = False         # <- set to True when compute() and run() are ready
    progress = 0                # <- 0..100, shown on the coming-soon screen

    # def compute(self, p: Problem, n: int) -> float:
    #     """Return the Simpson estimate. Raise ValueError(t("...")) if n is not allowed."""
    #     ...
    #
    # def run(self) -> None:
    #     """Interactive screen. Reuse: ask_problem(), ask_n_list(), ask_tol(),
    #     title(), step(), say(), show_errors(p, estimate), t("key")."""
    #     LOG.clear()
    #     title(t("menu_simp"))
    #     p = ask_problem()
    #     for n in ask_n_list("2"):
    #         I = self.compute(p, n)
    #         step(...)
    #         show_errors(p, I)


# ============================================================================
# SECTION 4 - GABUNGAN / COMBINED  (Simpson 1/3 + 3/8)  TEAMMATE B  (belum dikerjakan)
# ============================================================================
add_strings({
    # TEAMMATE B: add your own texts here (same format as above).
})


class CombinedModule(MethodModule):
    key = "combined"
    title_key = "menu_comb"
    owner = "Anggota Tim B"     # <- TEAMMATE B: write your name
    implemented = False         # <- set to True when ready
    progress = 0

    # Rule from the slides (47): n even -> Simpson 1/3 everywhere;
    # n odd and n > 1 -> Simpson 3/8 on the last 3 segments + 1/3 on the rest; n = 1 -> trapezoid.
    # def compute(self, p: Problem, n: int) -> float: ...
    # def run(self) -> None: ...


# ============================================================================
# SECTION 5 - COMPARE + MAIN MENU
# ============================================================================
add_strings({
    "cmp_title": ("PERBANDINGAN METODE", "METHOD COMPARISON", "COMPARAISON DES MÉTHODES"),
    "cmp_head": ("--- n = {n} segmen ---", "--- n = {n} segments ---", "--- n = {n} segments ---"),
    "cmp_best": ("Paling akurat: {m}", "Most accurate: {m}", "Le plus précis : {m}"),
})

MODULES: List[MethodModule] = [TrapezoidModule(), SimpsonModule(), CombinedModule()]


def compare_all() -> None:
    LOG.clear()
    title(t("cmp_title"))
    p = ask_problem()
    ns = ask_n_list("6")
    for n in ns:
        say()
        say(t("cmp_head", n=n))
        say(f"  {'':<44}{'I':>14}{'Et':>12}{'|et| %':>10}")
        results: List[Tuple[float, str]] = []
        for m in MODULES:
            name = t(m.title_key)
            if not m.implemented:
                say(f"  {name:<44}{t('soon_tag')}")
                continue
            try:
                est = m.compute(p, n)
            except Exception as exc:  # noqa: BLE001  (one teammate's bug must not stop the demo)
                say(f"  {name:<44}{exc}")
                continue
            if p.exact is not None:
                rel = rel_err_pct(p.exact, est)
                say(f"  {name:<44}{est:>14.6f}{p.exact - est:>12.6f}{rel:>10.4f}")
                results.append((rel, name))
            else:
                say(f"  {name:<44}{est:>14.6f}")
        if len(results) >= 2:
            say(t("cmp_best", m=min(results)[1]))
    out()
    ask(t("press_enter"))


def choose_language() -> None:
    out()
    out(t("lang_prompt"))
    for i, code in enumerate(LANGS, 1):
        out(f"  {i}) {LANG_NAMES[code]}")
    while True:
        c = ask(">", "1").lower()
        if c in ("1", "2", "3") or c in LANGS:
            set_lang(LANGS[int(c) - 1] if c.isdigit() else c)
            out(t("lang_set"))
            return
        out(t("bad_choice"))


def banner() -> None:
    out()
    out("          ___________________")
    out("         /|    |    |    |   |\\")
    out("        / |    |    |    |   | \\")
    out("       /__|____|____|____|___|__\\")
    out()
    out("   " + t("app_title"))
    out("   " + t("app_sub"))


def main_menu() -> None:
    banner()
    while True:
        out()
        out("=" * 50)
        out("  " + t("menu_title"))
        out("=" * 50)
        for i, m in enumerate(MODULES, 1):
            tag = "" if m.implemented else "  " + t("soon_tag")
            out(f"  {i}) {t(m.title_key)}{tag}")
        k = len(MODULES)
        out(f"  {k + 1}) {t('menu_cmp')}")
        out(f"  {k + 2}) {t('menu_lang')}")
        out(f"  0) {t('menu_exit')}")
        choice = ask(t("menu_choice"))
        if choice == "0":
            out(t("bye"))
            return
        if choice == str(k + 2):
            choose_language()
        elif choice.isdigit() and 1 <= int(choice) <= k + 1:
            try:
                MODULES[int(choice) - 1].run() if int(choice) <= k else compare_all()
            except (KeyboardInterrupt, EOFError):
                raise
            except Exception as exc:  # noqa: BLE001
                name = t(MODULES[int(choice) - 1].title_key) if int(choice) <= k else t("menu_cmp")
                out(t("module_error", name=name, err=exc))
        else:
            out(t("bad_choice"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Numerical integration calculator / Kalkulator integrasi numerik")
    ap.add_argument("--lang", choices=LANGS, help="id (default), en, fr")
    args = ap.parse_args()
    try:
        if args.lang:
            set_lang(args.lang)
        else:
            choose_language()
        main_menu()
    except (KeyboardInterrupt, EOFError):
        out()
        out(t("bye"))


if __name__ == "__main__":
    main()
