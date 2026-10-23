"""Admitted payload APIs must not import unrelated enum siblings."""
from pathlib import Path


def variant_cases(base):
    base = Path(base) / "variant-sources"
    base.mkdir(exist_ok=True)
    sources, bodies = [], {}
    siblings = ("SharedOwner", "SharedView", "SharedAccess", "SharedAtomicU32",
                "SharedAtomicU64", "UnsafePtr", "u64", "u8[]")
    for shape in ("value", "reference", "slice", "nested", "return"):
        declarations, checks = [], []
        for index, sibling in enumerate(siblings):
            enum = f"Payload{index}"
            payload = enum + ".Public"
            ctype = enum + "_g_Public_p"
            name = f"payload_{index}"
            declarations.append(f"enum {enum} {{ Public {{ value: u32 }}, Hidden {{ token: {sibling} }} }}")
            if shape == "value":
                declarations.append(f"export fn {name}(v: {payload}) -> {payload} {{ v }}")
                checks.append(f"{ctype} p{index} = {{ 42 }};\n"
                              f"{ctype} (*f{index})({ctype}) = {name};\n"
                              f"assert(f{index}(p{index}).value_g == 42);")
            elif shape == "reference":
                declarations.append(f"export fn {name}(v: const {payload}&) -> u32 {{ v.value }}")
                checks.append(f"{ctype} p{index} = {{ 42 }};\n"
                              f"uint32_t (*f{index})({ctype} *) = {name};\n"
                              f"assert(f{index}(&p{index}) == 42);")
            elif shape == "slice":
                declarations.append(f"export fn {name}(v: const {payload}[:]) -> u32 {{ v[0].value }}")
                checks.append(f"{ctype} p{index} = {{ 42 }};\n"
                              f"sl_{ctype} s{index} = {{ &p{index}, 1 }};\n"
                              f"uint32_t (*f{index})(sl_{ctype}) = {name};\n"
                              f"assert(f{index}(s{index}) == 42);")
            elif shape == "nested":
                outer = f"PublicBox{index}"
                declarations.append(f"struct {outer} {{ prefix: u8, payload: {payload} }}\n"
                                    f"export fn {name}(v: {outer}) -> {outer} {{ v }}")
                checks.append(f"{outer}_g p{index} = {{ 1, {{ 42 }} }};\n"
                              f"{outer}_g (*f{index})({outer}_g) = {name};\n"
                              f"p{index} = f{index}(p{index});\n"
                              f"assert(p{index}.prefix_g == 1 && p{index}.payload_g.value_g == 42);\n"
                              f"STATIC_ASSERT(sizeof({outer}_g) == 5, \"nested payload layout\");\n"
                              f"STATIC_ASSERT(offsetof({outer}_g, payload_g) == 1, \"nested payload offset\");")
            else:
                declarations.append(f"export fn {name}() -> {payload} {{ {payload} {{ 42 }} }}")
                checks.append(f"{ctype} (*f{index})(void) = {name};\n"
                              f"assert(f{index}().value_g == 42);")
            checks.append(f"STATIC_ASSERT(sizeof({ctype}) == 4, \"payload ABI\");")
        source = base / f"variant_{shape}.goose"
        source.write_text("\n".join(declarations) + "\n", encoding="utf-8")
        sources.append(source)
        bodies[source.stem] = ("int main(int argc, char **argv) {\ngoose_init(argc, argv);\n" +
                               "\n".join(checks) + "\nreturn 0;\n}\n")

    # A whole ordinary enum really does require every sibling. Exercise both
    # declaration orders with selected payload APIs sharing that same enum.
    declarations, checks = [], []
    for index in (0, 1):
        enum = f"Whole{index}"
        declarations.append(f"enum {enum} {{ Public {{ value: u32 }}, Other {{ value: u64 }} }}")
        selected = f"export fn selected_{index}(v: {enum}.Public) -> {enum}.Public {{ v }}"
        whole = f"export fn whole_{index}(v: {enum}) -> {enum} {{ v }}"
        declarations.extend((selected, whole) if index == 0 else (whole, selected))
        checks.append(f"{enum}_g_Public_p p{index} = {{ 42 }};\n"
                      f"assert(selected_{index}(p{index}).value_g == 42);\n"
                      f"{enum}_g w{index} = {{ 0 }};\n"
                      f"w{index}.tag = {enum}_g_Other_g_k; w{index}.u.v_Other_g.value_g = 55;\n"
                      f"w{index} = whole_{index}(w{index});\n"
                      f"assert(w{index}.u.v_Other_g.value_g == 55);")
    source = base / "variant_whole_enum.goose"
    source.write_text("\n".join(declarations) + "\n", encoding="utf-8")
    sources.append(source)
    bodies[source.stem] = ("int main(int argc, char **argv) {\ngoose_init(argc, argv);\n" +
                           "\n".join(checks) + "\nreturn 0;\n}\n")
    return sources, bodies
