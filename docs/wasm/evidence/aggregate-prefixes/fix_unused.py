from pathlib import Path
import json,shutil
p=Path(__file__).parent;r=Path('/home/dev/Projects/goose-wasm-backend')
rows=json.loads((p/'slot-forms01/results.json').read_text());assert len(rows)==15
assert all(x['native_run_exit']==0 and x['parent_run_exit']==1 and x['prototype_run_exit']==1 for x in rows)
for name in ['wasm_codegen.h','wasm_fixed.h','wasm_arrays.h','wasm_support.h']:shutil.copy2(r/'src'/name,p/'build01'/(name+'.txt'))
f=r/'src/wasm_codegen.h';s=f.read_text();needle='    void ZeroFixed(const FixedPlace &destination, uint32_t bytes, Line line);';assert s.count(needle)==1;s=s.replace(needle,needle+'\n    void ZeroUnusedInlineArray(FixedPlace destination, uint64_t count, Line line);');f.write_text(s)
f=r/'src/wasm_fixed.h';s=f.read_text();needle='inline void WasmCodeGen::InlineArrayLiteral('
pos=s.index(needle)
helper='''inline void WasmCodeGen::ZeroUnusedInlineArray(FixedPlace destination, uint64_t count, Line line) {
    auto array = destination.type;
    if (!InlineArray(array) || array->arr->akind != A_LIMITED) return;
    auto capacity = (uint64_t)ArrSize(array->arr);
    // A full literal has no suffix. An oversized push literal cannot complete.
    if (count >= capacity) return;
    auto image = RequireFixed(array, line), stride = RequireFixed(array->arr->sub, line);
    auto begin = (uint64_t)IntSize(LenStore(array->arr)) + count * stride;
    auto bytes = (capacity - count) * stride;
    if (!destination.bounded || begin > image || bytes > image - begin ||
        begin > UINT32_MAX - destination.offset)
        Fail(line, "unused array slots exceed their fixed owner image");
    destination.offset += (uint32_t)begin; destination.type = array->arr->sub;
    ZeroFixed(destination, (uint32_t)bytes, line);
}

'''
s=s[:pos]+helper+s[pos:]
needle='''            PushArray(place, value, nullptr, value->line, scratch);
        }
    }
}

inline void WasmCodeGen::ConstructFields''';replace='''            PushArray(place, value, nullptr, value->line, scratch);
        }
        ZeroUnusedInlineArray(place.image, literal->elems.size(), literal->line);
    }
}

inline void WasmCodeGen::ConstructFields''';assert s.count(needle)==1;s=s.replace(needle,replace)
s=s.replace('    if (each && !count) return;','    if (each && !count) { ZeroUnusedInlineArray(destination.place, count, line); return; }')
needle='''            if (count) loop([&] { copy(item); });
        });
    }
}

inline void WasmCodeGen::ConstructAggregateArray''';replace='''            if (count) loop([&] { copy(item); });
        });
    }
    ZeroUnusedInlineArray(destination.place, count, line);
}

inline void WasmCodeGen::ConstructAggregateArray''';assert s.count(needle)==1;s=s.replace(needle,replace)
needle='''        } else ConstructFixed(child, init);
    }
}

inline void WasmCodeGen::CopyFixed''';replace='''        } else ConstructFixed(child, init);
    }
    ZeroUnusedInlineArray(destination.place, literal->elems.size(), literal->line);
}

inline void WasmCodeGen::CopyFixed''';assert s.count(needle)==1;s=s.replace(needle,replace)
needle='''                PrepareArrayLengthStore(place); code.I64(0); StoreArrayLength(place);
            }
            return;
        }
        Fail(source->line, "this default''';replace='''                PrepareArrayLengthStore(place); code.I64(0); StoreArrayLength(place);
                ZeroUnusedInlineArray(destination, 0, source->line);
            }
            return;
        }
        Fail(source->line, "this default''';assert s.count(needle)==1;s=s.replace(needle,replace);f.write_text(s)
f=r/'src/wasm_arrays.h';s=f.read_text();a=s.index('inline void WasmCodeGen::InitByteString(');b=s.index('\ninline void WasmCodeGen::InitFilledArray(',a);body=s[a:b]
body=body.replace('        if (!count) return;','        if (!count) { ZeroUnusedInlineArray(*destination, count, literal->line); return; }')
needle='''                  (uint32_t)count, literal->line, true);
        return;''';replace='''                  (uint32_t)count, literal->line, true);
        ZeroUnusedInlineArray(*destination, count, literal->line);
        return;''';assert body.count(needle)==1;body=body.replace(needle,replace)
needle='''    auto base = Local(WasmModule::I64);
    if (InlineArray(array))''';replace='''    auto base = Local(WasmModule::I64);
    FixedPlace inlineImage {array, NoLocal};
    if (InlineArray(array))''';assert body.count(needle)==1;body=body.replace(needle,replace)
needle='''        code.Set(header);
        if (array->arr->akind == A_LIMITED)''';replace='''        code.Set(header);
        inlineImage = {array, header, 0, memory, packed, true};
        if (array->arr->akind == A_LIMITED)''';assert body.count(needle)==1;body=body.replace(needle,replace)
body=body.replace('    if (!count) return;','    if (!count) { if (InlineArray(array)) ZeroUnusedInlineArray(inlineImage, count, literal->line); return; }')
needle='''              (uint32_t)count, literal->line, true);
}''';replace='''              (uint32_t)count, literal->line, true);
    if (InlineArray(array)) ZeroUnusedInlineArray(inlineImage, count, literal->line);
}''';assert body.count(needle)==1;body=body.replace(needle,replace);s=s[:a]+body+s[b:]
a=s.index('inline void WasmCodeGen::InitFilledArray(');b=s.index('\ninline void WasmCodeGen::InitDataArray(',a);body=s[a:b]
needle='''    auto base = destination ? fixedfillbase : Local(WasmModule::I64);
    if (InlineArray(array))''';replace='''    auto base = destination ? fixedfillbase : Local(WasmModule::I64);
    FixedPlace inlineImage = destination ? *destination : FixedPlace {array, NoLocal};
    if (InlineArray(array))''';assert body.count(needle)==1;body=body.replace(needle,replace)
needle='''            Address(*slot); code.Set(header);
            if (array->arr->akind == A_LIMITED)''';replace='''            Address(*slot); code.Set(header);
            inlineImage = {array, header, 0, memory, false, true};
            if (array->arr->akind == A_LIMITED)''';assert body.count(needle)==1;body=body.replace(needle,replace)
body=body.replace('    if (!count) return;','    if (!count) { if (InlineArray(array)) ZeroUnusedInlineArray(inlineImage, count, literal->line); return; }')
needle='''    Branch(head); Close(); Close();
}''';replace='''    Branch(head); Close(); Close();
    if (InlineArray(array)) ZeroUnusedInlineArray(inlineImage, count, literal->line);
}''';assert body.count(needle)==1;body=body.replace(needle,replace);s=s[:a]+body+s[b:];f.write_text(s)
print('shared suffix clear added after successful construction; no stored-copy changes')
