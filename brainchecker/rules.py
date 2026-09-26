"""What counts as a decision, and whether it is critical.

Rules only, never AI (protocol §3): a script cannot know intent, but decisions in a
modelling repo have addresses and shapes. A line or hunk is a decision when it carries
one of these signatures:

    value      a literal given to a named setting (parameter, bound, tolerance, window, colour)
    equation   an MTK equation, a connection, a component, an ODE right-hand side
    selection  a list of runs / models / patients / panels, a pin, a loop over literals
    rule       a gate, an assert, an objective, a metric, a threshold comparison
    claim      prose that states a number or a finding, *and* is reused elsewhere
    new-file   a new file in a pillar folder
    code       any other non-trivial change inside a critical-by-default file

Criticality follows the form: the path map sets a default, and the "critical when"
conditions and the "flag wherever it appears" patterns override it upward.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

NUM = r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?"
RE_NUM = re.compile(r"(?<![\w.])" + NUM + r"(?![\w.])")
RE_HEX = re.compile(r"#[0-9A-Fa-f]{6}\b")
RE_ASSIGN = re.compile(r"^\s*(?:const\s+|global\s+|local\s+|export\s+)?([A-Za-z_][\w.]*)\s*(?:::\s*[\w{}]+)?\s*=(?!=)\s*(.+)$")
RE_PAIR = re.compile(r"[:\"']([A-Za-z_]\w*)[\"']?\s*=>\s*([^,)\]}]+)")
RE_KWDEF = re.compile(r"\b([A-Za-z_]\w*)\s*=\s*(" + NUM + r"|:\w+|\"[^\"]*\"|true|false)")
RE_ENV = re.compile(r"get\(\s*ENV\s*,\s*\"(\w+)\"\s*,\s*\"([^\"]*)\"\s*\)")
RE_CLAMP = re.compile(r"clamp\([^,]+,\s*(" + NUM + r")\s*,\s*(" + NUM + r")\s*\)")
RE_FUNC = re.compile(r"^\s*(?:function\s+([\w.!]+)|def\s+(\w+)|([\w.!]+)\([^)]*\)\s*=(?!=))")
RE_EQ = re.compile(r"(?:^|[^=!~<>])~(?!=)")
RE_MTK = re.compile(r"\b(connect\(|@named\b|@variables\b|@parameters\b|@components\b|@equations\b|@mtkmodel\b|ODESystem\(|System\()")
RE_ODE = re.compile(r"\bdu\[\s*\w+\s*\]\s*=(?!=)|\bD\([^)]*\)\s*~")
RE_GATE = re.compile(r"(@assert\b|\bassert\b|\berror\(|\bthrow\(|\braise\b|\bexit\(\s*[1-9])")
RE_COND = re.compile(r"^\s*(?:if|elseif|elif|while)\b.*(?:<=|>=|<|>|==|!=)")
RE_METRIC = re.compile(r"(objective|loss|cost|score|rmse|metric|adjusted_rand|\bari\b|verify|gate|penalty|breakpoint|residual|likelihood)", re.I)
RE_SEL_NAME = re.compile(r"(?i)(?:^|_)(models?|run_ids?|runs|patients?|decks?|deck_choice|families|variants|sweeps|panels|figures|roster|sim_stamp|pin|experiments?|run_id_choice)(?:$|_)")
RE_PARAM_NAME = re.compile(r"(_v$|^FIT_|_LO$|_HI$|_MIN$|_MAX$|BOUND|^u0|A_baseline|^P0_|_START$)")
RE_TOL_NAME = re.compile(r"(tol|abstol|reltol|dtmax|maxiters|max_cycles|max_iter|atol|rtol|steady|clamp|TIMEOUT)", re.I)
RE_FOR_LIT = re.compile(r"^\s*for\s+\w+\s+in\s+[\[(]([^\]\)]+)[\])]")
RE_SH_FOR = re.compile(r"^\s*for\s+\w+\s+in\s+((?:[\w.\"'-]+\s+){1,}[\w.\"'-]+)\s*;?\s*(?:do)?\s*$")
RE_FINDING = re.compile(r"\b(STALE|refuted|confirmed|proves?|shows? that|is the reason|because|never|always|cannot|does not|doesn't|is wrong|is right|matches|agrees|disagrees|dominat|identical|verified)\b", re.I)
RE_TRIVIAL = re.compile(r"^\s*(?:$|#|//|using\b|import\b|from\s+\S+\s+import|include\(|println\(|@info\b|@debug\b|@warn\b|print\(|logging\.|end\s*$|\)\s*$|\]\s*$|}\s*$)")
RE_CALL = re.compile(r"\b([a-zA-Z_][\w!]*)\(")
KEYWORDS = {"if", "for", "while", "function", "return", "elseif", "print", "println", "string", "get",
            "haskey", "isfile", "joinpath", "length", "size", "min", "max", "abs", "round", "Dict",
            "Symbol", "String", "parse", "float", "Float64", "Int", "range", "enumerate", "zip",
            "push!", "append!", "map", "filter", "sum", "any", "all", "isnothing", "something",
            "tuple", "NamedTuple", "Tuple", "Vector", "Array", "collect", "first", "last",
            "sprintf", "format", "len", "str", "int", "list", "dict", "sorted", "open", "isdefined"}

KIND_ORDER = ["equation", "rule", "selection", "value", "claim", "code", "new-file"]


@dataclass
class Sig:
    kind: str
    line: int | None
    text: str
    symbol: str | None = None
    detail: str = ""
    param: bool = False              # a model parameter, bound or initial condition
    tolerance: bool = False          # tolerance / dtmax / maxiters / clamp
    compared: bool = False           # changes what is compared, or the comparison metric
    gate: bool = False
    numbers: list[str] = field(default_factory=list)


def lang(path: str) -> str:
    p = path.lower()
    if p.endswith(".jl"):
        return "julia"
    if p.endswith(".py"):
        return "python"
    if p.endswith((".sh", ".bash")):
        return "shell"
    if p.endswith((".md", ".typ", ".tex", ".txt", ".rst")):
        return "prose"
    if p.endswith((".toml", ".json", ".yml", ".yaml")):
        return "config"
    return "other"


def strip_strings(s: str) -> str:
    return re.sub(r"\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'", '""', s)


def code_part(s: str, language: str) -> str:
    """The line without its trailing comment (strings kept intact for literals)."""
    if language in ("julia", "python", "shell", "config"):
        out, q = [], None
        for i, ch in enumerate(s):
            if q:
                out.append(ch)
                if ch == q and s[i - 1] != "\\":
                    q = None
                continue
            if ch in "\"'":
                q = ch
            elif ch == "#":
                break
            out.append(ch)
        return "".join(out)
    return s


def comment_part(s: str, language: str) -> str:
    code = code_part(s, language)
    rest = s[len(code):]
    return rest.lstrip("#").strip() if rest.startswith("#") else ""


def claim_numbers(text: str) -> list[str]:
    """Numbers in prose worth checking for reuse: decimals, or 3+ significant digits,
    not dates, years, line references or section numbers."""
    out = []
    for m in re.finditer(r"(?<![\w.:/-])(\d+\.\d+|\d{3,})(?![\w.:/-]*\d)", text):
        tok = m.group(1)
        if re.fullmatch(r"20\d\d|19\d\d", tok):
            continue
        if "." not in tok and not re.match(r"\s*(?:%|x\b|×|Hz|s\b|ms\b|mmHg|mL|ml|bpm|min|dyn|cm|mm|MB|GB)",
                                           text[m.end():m.end() + 6]):
            continue                                          # ids, counts, sizes without a unit
        before = text[max(0, m.start() - 2):m.start()]
        if before.endswith((".jl:", ".py:", "L")):
            continue
        out.append(tok)
    return out


COSMETIC = {"label", "labels", "xlabel", "ylabel", "zlabel", "title", "font", "fontsize", "legendfontsize",
            "titlefontsize", "tickfontsize", "guidefontsize", "margin", "row", "col", "frameon",
            "borderaxespad", "zorder", "textposition", "prefix", "suffix", "fmt", "size", "framestyle",
            "grid", "dpi", "file", "name", "names", "digits", "width", "height", "showlegend",
            "hovertemplate", "mode", "source", "range", "text", "loc", "ha", "va", "rotation", "pad",
            "bbox_inches", "delimiter", "encoding", "dtype", "sep", "end", "flush", "indent", "path",
            "filename", "outfile", "stamp", "commit"}

def _cosmetic(name: str) -> bool:
    n = name.split(".")[-1]
    return n in COSMETIC or n.endswith(("fontsize", "_font", "label", "xlab", "ylab")) or n in ("xlab", "ylab")


TRIVIAL_NUMS = {"0", "1", "2", "0.0", "1.0", "2.0", "0.5", "-1", "-1.0"}


def _literal(rhs: str) -> bool:
    """A named setting given a literal: the whole value is a number (maybe with a unit),
    a string, a symbol, a colour or a bool; or an expression carries a non-trivial number."""
    raw = rhs.strip().rstrip(",;").strip()
    r = strip_strings(raw)
    if re.fullmatch(r"[-+]?" + NUM + r"(\s*[*/]\s*[A-Za-z_][\w.]*)*", r):
        return True
    if re.fullmatch(r'"[^"$]{1,60}"|:\w+|true|false|True|False|#[0-9A-Fa-f]{6}', raw):
        return True
    if "$" in raw and not RE_NUM.search(strip_strings(raw)):
        return False                                          # an interpolated string
    if RE_HEX.search(raw):
        return True
    r2 = re.sub(r"(?<=[\w\])])\[[^\]]*\]", "", r)          # indexing is not a setting
    r2 = re.sub(r"\b(axis|dims|ndims|digits|dtype|level)\s*=\s*" + NUM, "", r2)
    return any(m.group(0).lstrip("+") not in TRIVIAL_NUMS for m in RE_NUM.finditer(r2))


def _segments(rhs: str) -> list[str]:
    """Split at top-level commas."""
    out, depth, cur, q = [], 0, [], None
    for ch in rhs:
        if q:
            cur.append(ch)
            if ch == q:
                q = None
            continue
        if ch in "\"'":
            q = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(cur)); cur = []
            continue
        cur.append(ch)
    if "".join(cur).strip():
        out.append("".join(cur))
    return out


def _collection_items(rhs: str) -> list[str] | None:
    """Items of a literal collection; None for comprehensions and computed lists."""
    r = rhs.strip()
    m = re.match(r"^(?:Set\(|Tuple\(|\(|\[|\{)(.*)(?:\)|\]|\})\s*,?\s*$", r)
    if not m or re.search(r"\bfor\b", m.group(1)):
        return None
    items = [x.strip() for x in _segments(m.group(1)) if x.strip()]
    # a literal item: a number (with a unit), a string, a symbol, a name, or k = / k => / k: one of those
    lit = re.compile(r'(?:[\w"\':.]+\s*(?:=>|=|:)\s*)?(?:[-+]?' + NUM + r'(?:\s*[*/]\s*[A-Za-z_]\w*)?|"[^"$]*"|\'[^\']*\'|:?[A-Za-z_]\w*)')
    if len(items) < 2 or not all(lit.fullmatch(i) for i in items):
        return None
    return items


def _numeric_item(i: str) -> bool:
    v = re.split(r"=>|=|:", i)[-1].strip() if re.match(r'^[\w"\']+\s*(=>|=|:)', i) else i
    return bool(RE_NUM.fullmatch(v.split("*")[0].split("/")[0].strip()))


def scan_code_line(path: str, ln: int, raw: str, language: str) -> list[Sig]:
    code = code_part(raw, language)
    if not code.strip():
        return []
    sigs: list[Sig] = []
    stripped = strip_strings(code)

    # equations / topology (Julia) and ODE right-hand sides
    if language == "julia" and (RE_EQ.search(stripped) or RE_MTK.search(stripped) or RE_ODE.search(stripped)):
        sigs.append(Sig("equation", ln, raw.strip(), detail="equation or component"))

    # gates and thresholds
    if RE_GATE.search(stripped):
        sigs.append(Sig("rule", ln, raw.strip(), detail="gate", gate=True))
    elif RE_COND.search(stripped) and (RE_NUM.search(stripped) or re.search(r"\b[A-Z][A-Z0-9_]{2,}\b", stripped)):
        sigs.append(Sig("rule", ln, raw.strip(), detail="threshold"))

    fm = RE_FUNC.match(code)
    if fm:
        fname = next(g for g in fm.groups() if g)
        if RE_METRIC.search(fname):
            sigs.append(Sig("rule", ln, raw.strip(), symbol=fname, detail="objective or metric", compared=True))
        for k, v in RE_KWDEF.findall(code):                          # keyword defaults
            sigs.append(Sig("value", ln, raw.strip(), symbol=k, detail=f"default {k} = {v}",
                            param=bool(RE_PARAM_NAME.search(k)), tolerance=bool(RE_TOL_NAME.search(k))))

    for env, val in RE_ENV.findall(code):
        if RE_NUM.fullmatch(val.strip()) or val.strip() in ("0", "1"):
            sigs.append(Sig("value", ln, raw.strip(), symbol=env, detail=f"env default {env}={val}",
                            tolerance=bool(RE_TOL_NAME.search(env))))

    for lo, hi in RE_CLAMP.findall(stripped):
        if not (float(lo) == 0 and float(hi) == 1):
            sigs.append(Sig("value", ln, raw.strip(), symbol="clamp", detail=f"clamp [{lo}, {hi}]", tolerance=True))

    m = RE_ASSIGN.match(code)
    if m and _cosmetic(m.group(1)) and "," not in m.group(2):
        m = None
    if m and not fm and not re.match(r"^\s*for\b", code):
        name, rhs_all = m.group(1), m.group(2)
        segs = _segments(rhs_all) or [rhs_all]
        rhs = segs[0].strip()
        if rhs.count("(") < rhs.count(")"):             # the line closes a call: `x = 1)`
            rhs = rhs[:len(rhs) - (rhs.count(")") - rhs.count("("))]
        for seg in segs[1:]:
            km = re.match(r"^\s*([A-Za-z_]\w*)\s*=(?!=)\s*(.+)$", seg)
            if km and not _cosmetic(km.group(1)) and _literal(km.group(2).rstrip(")")):
                k = km.group(1)
                sigs.append(Sig("value", ln, raw.strip(), symbol=k, detail=f"{k} = {km.group(2).strip()[:30]}",
                                param=bool(RE_PARAM_NAME.search(k)), tolerance=bool(RE_TOL_NAME.search(k))))
        items = _collection_items(rhs)
        if items and (RE_SEL_NAME.search(name) or not all(_numeric_item(i) for i in items)):
            nonnum = [i for i in items if not _numeric_item(i)]
            named = [i for i in nonnum if re.search(r'["\':]', i)]   # quoted or symbols, not bare variables
            if named or RE_SEL_NAME.search(name):
                sigs.append(Sig("selection", ln, raw.strip(), symbol=name, detail=f"{len(items)} items",
                                compared=bool(RE_SEL_NAME.search(name))))
            elif not nonnum:
                sigs.append(Sig("value", ln, raw.strip(), symbol=name, detail="numeric vector",
                                param=bool(RE_PARAM_NAME.search(name)), tolerance=bool(RE_TOL_NAME.search(name))))
        elif RE_SEL_NAME.search(name) and _literal(rhs):
            sigs.append(Sig("selection", ln, raw.strip(), symbol=name, detail="selection", compared=True))
        elif not _cosmetic(name) and _literal(rhs) and not re.fullmatch(r"\s*(true|false|nothing|None|\"\")\s*", rhs):
            sigs.append(Sig("value", ln, raw.strip(), symbol=name, detail="named value",
                            param=bool(RE_PARAM_NAME.search(name)), tolerance=bool(RE_TOL_NAME.search(name))))

    for pm in RE_PAIR.finditer(code):
        key = pm.group(1)
        rest = code[pm.start(2):]
        val = (_segments(rest) or [rest])[0].strip()
        if val.count(")") > val.count("("):
            val = val[:len(val) - (val.count(")") - val.count("("))]
        if not _cosmetic(key) and _literal(val):
            sigs.append(Sig("value", ln, raw.strip(), symbol=key, detail=f":{key} => {val.strip()[:30]}",
                            param=bool(RE_PARAM_NAME.search(key)), tolerance=bool(RE_TOL_NAME.search(key))))

    fl = RE_FOR_LIT.match(code) if language != "shell" else RE_SH_FOR.match(code)
    if fl:
        items = [x for x in re.split(r"[\s,]+", fl.group(1)) if x]
        if len(items) >= 2 and all(re.fullmatch(r"[\w\"'.:+-]+", x) for x in items):
            sigs.append(Sig("selection", ln, raw.strip(), detail="loop over literals",
                            compared=any(re.fullmatch(r"\"?\d{3}\"?|:?m\d\w*", i) for i in items)))
    if language == "shell":
        sm = re.match(r"^\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)=([^\s;]+)", code)
        if sm and _literal(sm.group(2)):
            sigs.append(Sig("value", ln, raw.strip(), symbol=sm.group(1), detail="shell value",
                            tolerance=bool(RE_TOL_NAME.search(sm.group(1)))))
    return sigs


def scan_text(path: str, text: str) -> list[Sig]:
    """Every signature in a whole file (review mode). Claims are returned with their
    numbers; whether they count depends on reuse, decided by the caller."""
    language = lang(path)
    sigs: list[Sig] = []
    in_block = None
    for i, raw in enumerate(text.splitlines(), start=1):
        s = raw.strip()
        if language == "julia":
            if in_block:
                if '"""' in s or "=#" in s:
                    in_block = None
                _prose(sigs, i, s)
                continue
            if s.startswith('"""') and s.count('"""') == 1 or s.startswith("#=") and "=#" not in s:
                in_block = True
                _prose(sigs, i, s.strip('"#= '))
                continue
        if language == "python":
            if in_block:
                if '"""' in s or "'''" in s:
                    in_block = None
                _prose(sigs, i, s)
                continue
            if (s.startswith('"""') or s.startswith("'''")) and s.count(s[:3]) == 1:
                in_block = True
                _prose(sigs, i, s.strip("\"' "))
                continue
        if language in ("prose",):
            if s.startswith("```"):
                in_block = not in_block
                continue
            if not in_block:
                _prose(sigs, i, s)
            continue
        if language in ("julia", "python", "shell", "config"):
            c = comment_part(raw, language)
            if c:
                _prose(sigs, i, c)
            sigs.extend(scan_code_line(path, i, raw, language))
    return sigs


RE_CODE_STRONG = re.compile(r"^\s*(?:end|if|elseif|else|for|while|return|const|function|def|using|import|"
                            r"let|local|@\w+|[\w.!]+\(.*\)\s*[,;]?\s*$|[\w.\[\]:\"]+\s*=>)|\"\w+\":\s*[{\[\"]|\|\||&&")
RE_CODE_WEAK = re.compile(r"(=>|~|::|[\w!]\(|^\s*[\w.\[\]:]+\s*=|;\s*$)")


def _prose(sigs: list[Sig], ln: int, text: str):
    words = re.findall(r"[A-Za-z]{3,}", strip_strings(text))
    if RE_CODE_STRONG.search(text) or (RE_CODE_WEAK.search(text) and len(words) < 5):
        return                                                # commented-out code
    nums = claim_numbers(text)
    if nums or RE_FINDING.search(text):
        sigs.append(Sig("claim", ln, text.strip()[:240], detail="prose claim", numbers=nums))


def call_sequence(lines: list[str]) -> list[str]:
    seq = []
    for l in lines:
        for m in RE_CALL.finditer(strip_strings(code_part(l, "julia"))):
            if m.group(1) not in KEYWORDS:
                seq.append(m.group(1))
    return seq


def trivial(line: str) -> bool:
    return bool(RE_TRIVIAL.match(line))


def decision_id(path: str, kind: str, key: str) -> str:
    norm = re.sub(r"\s+", " ", key.strip())
    return "D-" + hashlib.sha1(f"{path}|{kind}|{norm}".encode()).hexdigest()[:8]


def primary_kind(sigs: list[Sig]) -> str:
    kinds = {s.kind for s in sigs}
    for k in KIND_ORDER:
        if k in kinds:
            return k
    return "code"


def criticality(target, path: str, sigs: list[Sig], extra: list[str] | None = None,
                generated: bool = False) -> tuple[bool, list[str], str, str]:
    """(critical, reasons, path level, path-map row)."""
    level, row = target.path_level(path)
    reasons: list[str] = []
    if level == "critical":
        reasons.append(f"path map: {row}")
    for s in sigs:
        if s.kind == "equation":
            reasons.append("changes a model equation, the topology or a constitutive law")
        if s.param and not generated:
            reasons.append("changes a parameter value, a bound or an initial condition")
        if s.tolerance:
            reasons.append("flag: a changed tolerance, dtmax, maxiters or clamp")
        if s.compared:
            reasons.append("changes what is compared with what, or the comparison metric")
    reasons.extend(extra or [])
    reasons = list(dict.fromkeys(reasons))
    return (bool(reasons), reasons, level, row)
