"""Numerical integration - criterion 1: trapezoid rule (single file).

Defaults reproduce slide "Aturan Trapesium - Contoh 21.1":
    f(x) = 0.2 + 25x - 200x^2 + 675x^3 - 900x^4 + 400x^5,  a = 0, b = 0.8

Examples
    python main.py                       # slide example, single segment
    python main.py --n 1 10              # single segment, then 10 segments
    python main.py --b 1.2 --n 10        # change the upper limit to 1.2
    python main.py --expr "exp(-x**2)" --a 0 --b 1 --n 4
    python main.py --coeffs 1 2 3 --a 0 --b 2   # 1 + 2x + 3x^2

Sections of this file
    1. Core data structures (Polynomial, Problem, Step, Result)
    2. Method base class + registry   <- add Simpson / combined here later
    3. Trapezoid rule
    4. Advisor ("which method works?")
    5. Report printing
    6. Command-line interface
"""
from __future__ import annotations

import argparse
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Dict, Iterator, List, Optional, Sequence, Tuple


# ==========================================================================
# 1. CORE DATA STRUCTURES
# ==========================================================================
class Polynomial:
    """Polynomial with coeffs[i] = coefficient of x**i (ascending order)."""

    def __init__(self, coeffs: Sequence[float]):
        self.coeffs = [float(c) for c in coeffs]
        while len(self.coeffs) > 1 and self.coeffs[-1] == 0:
            self.coeffs.pop()

    def __call__(self, x: float) -> float:
        result = 0.0
        for c in reversed(self.coeffs):  # Horner's scheme
            result = result * x + c
        return result

    @property
    def degree(self) -> int:
        return len(self.coeffs) - 1

    def antiderivative(self) -> "Polynomial":
        return Polynomial([0.0] + [c / (i + 1) for i, c in enumerate(self.coeffs)])

    def __str__(self) -> str:
        out = ""
        for i, c in enumerate(self.coeffs):
            if c == 0:
                continue
            mag = f"{abs(c):g}"
            if i == 0:
                term = mag
            else:
                coef = "" if abs(c) == 1 else mag
                term = f"{coef}x" + (f"^{i}" if i > 1 else "")
            if not out:
                out = ("-" if c < 0 else "") + term
            else:
                out += (" - " if c < 0 else " + ") + term
        return out or "0"


def function_from_string(expr: str) -> Callable[[float], float]:
    """Turn e.g. '0.2 + 25*x - 200*x**2' into f(x). Only math.* names allowed."""
    namespace = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    code = compile(expr.replace("^", "**"), "<expr>", "eval")
    return lambda x: eval(code, {"__builtins__": {}}, {**namespace, "x": x})


@dataclass
class Problem:
    f: Callable[[float], float]
    a: float
    b: float
    label: str = "f(x)"
    exact: Optional[float] = None      # analytic integral, if known
    degree: Optional[int] = None       # polynomial degree, if known

    @classmethod
    def from_polynomial(cls, coeffs: Sequence[float], a: float, b: float,
                        exact: Optional[float] = None) -> "Problem":
        poly = Polynomial(coeffs)
        if exact is None:  # analytic value from the antiderivative
            F = poly.antiderivative()
            exact = F(b) - F(a)
        return cls(f=poly, a=a, b=b, label=f"f(x) = {poly}",
                   exact=exact, degree=poly.degree)


@dataclass
class Step:
    title: str
    lines: List[str]


@dataclass
class Result:
    method: str
    n: int
    estimate: float
    steps: List[Step]
    true_error: Optional[float] = None
    rel_true_error_pct: Optional[float] = None


def true_errors(exact: float, estimate: float) -> Tuple[float, float]:
    """Et = exact - approx ; relative true error in percent."""
    et = exact - estimate
    rel = et / exact * 100 if exact != 0 else math.inf
    return et, rel


# ==========================================================================
# 2. METHOD BASE CLASS + REGISTRY
# ==========================================================================
class Method(ABC):
    key: str = ""
    name: str = ""

    @abstractmethod
    def check(self, p: Problem) -> Tuple[bool, str]:
        """Return (applicable?, human-readable reason)."""

    @abstractmethod
    def estimate(self, p: Problem, n: int) -> float:
        """Fast numeric estimate only (used by the advisor)."""

    @abstractmethod
    def solve(self, p: Problem, n: int) -> Result:
        """Full step-by-step solution."""

    def n_ladder(self, max_n: int) -> Iterator[int]:
        """Segment counts the advisor tries, in order. Override if a method
        has constraints (e.g. Simpson 1/3 needs an even n)."""
        n = 1
        while n <= max_n:
            yield n
            n *= 2


REGISTRY: Dict[str, Method] = {}


def register(cls):
    """Class decorator: makes a Method visible to the advisor and the CLI."""
    REGISTRY[cls.key] = cls()
    return cls


# ==========================================================================
# 3. TRAPEZOID RULE (single segment n = 1, composite n > 1)
# ==========================================================================
MAX_ROWS = 12  # abbreviate the node table beyond this many rows


@register
class Trapezoid(Method):
    key = "trapezoid"
    name = "Trapezoid rule"

    def check(self, p: Problem) -> Tuple[bool, str]:
        if not p.a < p.b:
            return False, "Need a < b."
        probe = [p.a + (p.b - p.a) * i / 20 for i in range(21)]
        try:
            vals = [p.f(x) for x in probe]
        except Exception as exc:  # noqa: BLE001
            return False, f"f(x) cannot be evaluated on [a, b] ({exc})."
        if not all(math.isfinite(v) for v in vals):
            return False, "f(x) is not finite everywhere on [a, b] (singularity?)."
        msg = "f(x) is finite on [a, b], so the rule can be applied."
        if p.degree is not None:
            if p.degree <= 1:
                msg += " f is linear, so the rule is EXACT."
            else:
                msg += (f" f is a degree-{p.degree} polynomial; the rule is exact "
                        "only for degree <= 1, so a truncation error is expected.")
        return True, msg

    @staticmethod
    def _nodes(p: Problem, n: int) -> Tuple[float, List[float], List[float]]:
        h = (p.b - p.a) / n
        xs = [p.a + i * h for i in range(n + 1)]
        xs[-1] = p.b
        return h, xs, [p.f(x) for x in xs]

    def estimate(self, p: Problem, n: int) -> float:
        h, _, fs = self._nodes(p, n)
        return h / 2 * (fs[0] + 2 * math.fsum(fs[1:-1]) + fs[-1])

    def solve(self, p: Problem, n: int = 1) -> Result:
        if n < 1:
            raise ValueError("n must be >= 1")
        h, xs, fs = self._nodes(p, n)
        est = self.estimate(p, n)
        title = ("Trapezoid rule (single segment)" if n == 1
                 else f"Composite trapezoid rule ({n} segments)")
        steps: List[Step] = []

        steps.append(Step("Step 1 - Problem", [
            p.label, f"Interval [a, b] = [{p.a:g}, {p.b:g}]", f"Segments n = {n}"]))

        ok, why = self.check(p)
        steps.append(Step("Step 2 - Is the method applicable?",
                          [("YES: " if ok else "NO: ") + why]))

        steps.append(Step("Step 3 - Step size", [
            "h = (b - a) / n",
            f"h = ({p.b:g} - {p.a:g}) / {n} = {h:.6g}"]))

        rows = [f"x{i} = {x:.6g}   f(x{i}) = {fx:.6f}"
                for i, (x, fx) in enumerate(zip(xs, fs))]
        if len(rows) > MAX_ROWS:
            rows = rows[:4] + [f"... ({len(rows) - 6} more nodes) ..."] + rows[-2:]
        steps.append(Step("Step 4 - Evaluate f at the nodes", rows))

        if n == 1:
            steps.append(Step("Step 5 - Apply the formula", [
                "I ~= (b - a) * [f(a) + f(b)] / 2",
                f"I ~= {p.b - p.a:g} * ({fs[0]:.6f} + {fs[-1]:.6f}) / 2",
                f"I ~= {est:.6f}"]))
        else:
            interior = math.fsum(fs[1:-1])
            steps.append(Step("Step 5 - Apply the formula", [
                "I ~= (h/2) * [ f(x0) + 2 * (f(x1) + ... + f(x_{n-1})) + f(xn) ]",
                f"sum of interior f = {interior:.6f}",
                f"I ~= ({h:.6g}/2) * [ {fs[0]:.6f} + 2*{interior:.6f} + {fs[-1]:.6f} ]",
                f"I ~= {est:.6f}"]))

        et = rel = None
        if p.exact is not None:
            et, rel = true_errors(p.exact, est)
            steps.append(Step("Step 6 - Errors", [
                f"Analytic (true) value  I = {p.exact:.6f}",
                f"True error             Et = I - estimate = {p.exact:.6f} - {est:.6f} = {et:.6f}",
                f"Relative true error    |et| = |Et / I| x 100% = {abs(rel):.4f}%"]))
            r = abs(rel)
            if r < 1:
                note = "Good accuracy (< 1%)."
            elif r < 10:
                note = "Moderate accuracy; increase n for a better result."
            else:
                note = ("Poor accuracy: straight lines cannot follow this curve "
                        "over such wide segments. Increase n.")
            steps.append(Step("Step 7 - Interpretation", [note]))

        return Result(title, n, est, steps, et, rel)


# --- To add Simpson / combined later, write another class like this one: ---
# @register
# class Simpson13(Method):
#     key = "simpson13"; name = "Simpson 1/3 rule"
#     def check(self, p): ...
#     def estimate(self, p, n): ...
#     def solve(self, p, n): ...
#     def n_ladder(self, max_n): ...   # yield even n only


# ==========================================================================
# 4. ADVISOR - "which method works for this function?"
# ==========================================================================
@dataclass
class Verdict:
    method: str
    applicable: bool
    reason: str
    n_required: Optional[int] = None    # None -> tolerance not reached
    estimate: Optional[float] = None
    error_pct: Optional[float] = None
    basis: str = ""                     # "true error" or "estimated error"
    n1_error_pct: Optional[float] = None


def _error_pct(m: Method, p: Problem, n: int, est: float) -> Tuple[float, str]:
    if p.exact is not None:
        return abs(true_errors(p.exact, est)[1]), "true error"
    # No analytic value: compare with the estimate using twice as many segments.
    finer = m.estimate(p, 2 * n)
    err = abs((finer - est) / finer) * 100 if finer != 0 else abs(finer - est)
    return err, "estimated error"


def advise(p: Problem, tol_pct: float = 1.0, max_n: int = 1024) -> List[Verdict]:
    verdicts: List[Verdict] = []
    for m in REGISTRY.values():
        ok, why = m.check(p)
        v = Verdict(m.name, ok, why)
        if ok:
            for n in m.n_ladder(max_n):
                est = m.estimate(p, n)
                err, basis = _error_pct(m, p, n, est)
                if v.n1_error_pct is None:
                    v.n1_error_pct = err
                v.basis = basis
                v.estimate, v.error_pct = est, err
                if err <= tol_pct:
                    v.n_required = n
                    break
        verdicts.append(v)
    return verdicts


# ==========================================================================
# 5. REPORT PRINTING (ASCII only, safe for any console)
# ==========================================================================
LINE = "=" * 72


def print_solution(r: Result) -> None:
    print(f"\n{LINE}\n{r.method}\n{LINE}")
    for s in r.steps:
        print(f"\n{s.title}")
        for line in s.lines:
            print(f"    {line}")
    print(f"\n>>> RESULT: integral ~= {r.estimate:.6f}")


def print_advice(verdicts: List[Verdict], tol_pct: float) -> None:
    print(f"\n{LINE}\nWHICH METHOD WORKS?  (target: relative error <= {tol_pct:g}%)\n{LINE}")
    for v in verdicts:
        print(f"\n{v.method}")
        print(f"    Applicable : {'yes' if v.applicable else 'no'} - {v.reason}")
        if not v.applicable:
            continue
        if v.n1_error_pct is not None:
            print(f"    n = 1      : error = {v.n1_error_pct:.4f}% ({v.basis})")
        if v.n_required is not None:
            print(f"    Verdict    : WORKS with n = {v.n_required} segments "
                  f"(error = {v.error_pct:.4f}%, estimate = {v.estimate:.6f})")
        else:
            print(f"    Verdict    : tolerance NOT reached up to the tested n "
                  f"(last error = {v.error_pct:.4f}%)")


# ==========================================================================
# 6. COMMAND-LINE INTERFACE
# ==========================================================================
SLIDE_COEFFS = [0.2, 25, -200, 675, -900, 400]


def build_problem(args: argparse.Namespace) -> Problem:
    if args.expr:
        return Problem(f=function_from_string(args.expr), a=args.a, b=args.b,
                       label=f"f(x) = {args.expr}", exact=args.exact)
    return Problem.from_polynomial(args.coeffs or SLIDE_COEFFS, args.a, args.b,
                                   exact=args.exact)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", type=float, default=0.0, help="lower limit (default 0)")
    ap.add_argument("--b", type=float, default=0.8, help="upper limit (default 0.8)")
    ap.add_argument("--n", type=int, nargs="+", default=[1],
                    help="segment count(s) to solve step by step (default 1)")
    ap.add_argument("--coeffs", type=float, nargs="+",
                    help="polynomial coefficients, ascending powers (default: slide)")
    ap.add_argument("--expr", help="any expression in x, e.g. 'sin(x)+x**2'")
    ap.add_argument("--exact", type=float, help="analytic value (auto for polynomials)")
    ap.add_argument("--tol", type=float, default=1.0,
                    help="target relative error in %% for the advisor (default 1)")
    ap.add_argument("--max-n", type=int, default=1024, help="advisor search limit")
    args = ap.parse_args()

    problem = build_problem(args)
    method = REGISTRY["trapezoid"]          # criterion 1 only, for now

    for n in args.n:
        print_solution(method.solve(problem, n))
    print_advice(advise(problem, args.tol, args.max_n), args.tol)


if __name__ == "__main__":
    main()
