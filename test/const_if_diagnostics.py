#!/usr/bin/env python3
"""Const-if build-definition errors retain their source use, not Line{}.

Called by diagnostics_json.py in the normal runner. Run directly with the
compiler path; exact commands/results remain in build/gen/const-if-diagnostics.
"""
import json
from pathlib import Path
import subprocess
import sys


MESSAGE = "const if requires a bool constant expression"
TEMPLATES = {
    "minimal": "struct S { a:u8, const if CONDITION {b:u64,} else {c:u16,} } // diagnostic use\nfn main() {}\n",
    "function": """// function source context
fn main() {
    const if CONDITION { // diagnostic use
        print("yes");
    } else { print("no"); }
}
""",
    "fields": """// field source context
struct S {
    a: u8 = 1,
    const if CONDITION { b: u64 = 2, } else { c: u16 = 3, } // diagnostic use
}
fn main() {}
""",
    "constructor": """struct S { value: u32 }
// constructor source context
fn main() {
    let s = S {
        const if CONDITION { value: 1, } else { value: 2, } // diagnostic use
    };
    assert(s.value > 0);
}
""",
    "nested_function": """fn main() {
    const if true {
        // nested condition source context
        const if CONDITION { print("yes"); } else { print("no"); } // diagnostic use
    }
}
""",
    "nested_fields": """struct S {
    const if true {
        // nested field source context
        const if CONDITION { b: u64 = 2, } else { c: u16 = 3, } // diagnostic use
    }
}
fn main() {}
""",
    "nested_constructor": """struct S { value: u32 }
fn main() {
    let s = S {
        const if true {
            const if CONDITION { value: 1, } else { value: 2, } // diagnostic use
        }
    };
    assert(s.value > 0);
}
""",
}


def check_const_if_diagnostics(exe, base):
    base = Path(base).resolve()
    base.mkdir(parents=True, exist_ok=True)
    rows, failures = [], []

    def require(good, description, details):
        if not good:
            failures.append(description + "\n" + str(details))

    def run(args, expected):
        command = [str(exe), *map(str, args)]
        p = subprocess.run(command, capture_output=True, text=True,
                           errors="replace", timeout=90)
        rows.append(dict(command=command, returncode=p.returncode,
                         stdout=p.stdout, stderr=p.stderr))
        require(p.returncode == expected, "unexpected compiler exit", rows[-1])
        return p

    def diagnostic(entry, target, condition, flags, level):
        text = target.read_text(encoding="utf-8")
        lines = text.splitlines()
        lineno = next(i + 1 for i, line in enumerate(lines) if "diagnostic use" in line)
        line = lines[lineno - 1]
        col = line.index(condition, line.index("const if ") + len("const if ")) + 1
        ordinary = run(["check", level, *flags, entry], 1)
        structured = run(["check", "--diagnostics", "json", level, *flags, entry], 1)
        try:
            diags = json.loads(structured.stdout)
        except ValueError:
            require(False, "invalid diagnostic JSON", rows[-1])
            return
        errors = [d for d in diags if d.get("severity") == "error"]
        require(len(errors) == 1 and errors[0]["message"].startswith(MESSAGE),
                "wrong error", diags)
        if len(errors) != 1:
            return
        d = errors[0]
        require(Path(d.get("file", "")).resolve() == target and d.get("line") == lineno and
                d.get("col") == col and d.get("endLine") == lineno and
                d.get("endCol") == col + len(condition), "wrong source-use range", d)
        rendered = d["text"]
        require(rendered.startswith(f"{target}:{lineno}: error: {MESSAGE}") and
                line in rendered.splitlines()[1:], "missing source context", rendered)
        require(rendered + "\n" in ordinary.stderr,
                "text and JSON diagnostics disagree", ordinary.stderr + structured.stdout)

    try:
        for name, template in TEMPLATES.items():
            for mode in ("direct", "aliases", "imported_aliases", "imported_use"):
                directory = base / f"{name}-{mode}"
                directory.mkdir(exist_ok=True)
                entry = directory / "main.goose"
                target = directory / "consumer.goose" if mode == "imported_use" else entry
                condition, prefix = "build::WIDE", ""
                if mode == "aliases":
                    condition = "ALIAS"
                    prefix = "let CONFIG = build::WIDE;\nlet ALIAS = CONFIG;\n\n"
                elif mode in ("imported_aliases", "imported_use"):
                    condition = "settings::ALIAS"
                    prefix = "import config;\n\n"
                    (directory / "config.goose").write_text(
                        "// definition aliases in a different source file\n"
                        "let settings::CONFIG = build::WIDE;\n"
                        "let settings::ALIAS = settings::CONFIG;\n", encoding="utf-8")
                body = prefix + template.replace("CONDITION", condition)
                if mode == "imported_use":
                    body = body.replace("fn main()", "fn exercise()")
                    entry.write_text("import consumer;\nfn main() { exercise(); }\n", encoding="utf-8")
                target.write_text(body, encoding="utf-8")
                for level in ("-O0", "-O2"):
                    for value in ("1", '"not_bool"'):
                        diagnostic(entry, target, condition, ["--define", "WIDE=" + value], level)
                    for value in ("true", "false"):
                        p = run(["check", "--diagnostics", "json", level,
                                 "--define", "WIDE=" + value, entry], 0)
                        require(p.stdout.strip() == "[]", "boolean control was diagnosed", p.stdout)

        # An authored non-bool literal retains its own location and range.
        for name, template in TEMPLATES.items():
            for literal in ("1", '"not_bool"'):
                source = base / f"literal-{name}-{len(rows)}.goose"
                source.write_text(template.replace("CONDITION", literal), encoding="utf-8")
                for level in ("-O0", "-O2"):
                    diagnostic(source, source, literal, [], level)

        # The same immutable definition can fail at two distinct field uses
        # within one AST. A cached/mutated literal location cannot satisfy both.
        first, second = base / "first.goose", base / "second.goose"
        first.write_text("import second;\n\nstruct First {\n"
                         "    const if build::WIDE { a:u8, } else { b:u16, }\n"
                         "}\nfn main() {}\n", encoding="utf-8")
        second.write_text("// second source\nstruct Second {\n\n\n"
                          "    const if build::WIDE { a:u8, } else { b:u16, }\n}\n", encoding="utf-8")
        for level in ("-O0", "-O2"):
            p = run(["check", "--diagnostics", "json", level, "--define", "WIDE=1", first], 1)
            diags = json.loads(p.stdout)
            require({(Path(d.get("file", "")).resolve(), d.get("line")) for d in diags} ==
                    {(first, 4), (second, 5)} and
                    all(d["message"].startswith(MESSAGE) and "const if build::WIDE" in d["text"]
                        for d in diags),
                    "definition location leaked between uses", diags)

        # Integers and strings remain legal in typed comparisons. Boolean
        # operators validate both sides even when one would short-circuit.
        for condition, definition, expected in (
                ("build::WIDE == 1", "WIDE=1", 0),
                ('build::WIDE == "yes"', 'WIDE="yes"', 0),
                ("!build::WIDE", "WIDE=false", 0),
                ("true || build::WIDE", "WIDE=1", 1),
                ("false && build::WIDE", 'WIDE="no"', 1),
                ("build::WIDE == true", "WIDE=1", 1)):
            source = base / f"typed-{len(rows)}.goose"
            source.write_text(TEMPLATES["function"].replace("CONDITION", condition), encoding="utf-8")
            for level in ("-O0", "-O2"):
                if expected:
                    diagnostic(source, source, condition, ["--define", definition], level)
                else:
                    run(["check", level, "--define", definition, source], 0)
    finally:
        (base / "commands.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise RuntimeError("\n".join(failures))
    return len(rows)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    checks = check_const_if_diagnostics(Path(sys.argv[1]).resolve(),
                                       root / "build/gen/const-if-diagnostics")
    print(f"const if diagnostic locations: {checks} subprocess checks passed")
