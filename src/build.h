// Goose compiler — `goose build` (docs/design/packages.md §6): the C the
// compiler wrote, the runtime object and the native modules' response files,
// compiled and linked into an executable by the toolchain of toolchain.h.
// Intermediates live under GOOSE_HOME; the executable lands beside the root
// source unless -o says otherwise.
#pragma once

namespace goose {

// In main.cpp: the runtime's text hash, the runtime object's C, and a path's directory.
string RuntimeVersion();
string RuntimeObjectSource();
string DirOf(const string &path);

struct BuildOptions {
    bool debug = false;       // --debug: GS_DEBUG=1, debug information, no C optimization
    bool verbose = false;     // -v: print every command and what it prints
    bool dryrun = false;      // --dry-run: print the commands and run nothing
    bool standalone = false;  // --standalone: no runtime object
    string exe;               // -o: the executable; "" puts it beside the root source
    bool simd_feedback = false; // Clang vectorization remarks for simd functions
};

// Benchmark cache inputs captured before a build. Verify them again before
// publishing the stamp, so a concurrent edit cannot validate stale objects.
struct BuildInputStamp {
    string content;
    std::function<void()> verify;
};

inline string AbsolutePath(const string &path) {
    std::error_code ec;
    auto abs = filesystem::absolute(filesystem::path(path), ec);
    return ec ? path : abs.lexically_normal().string();
}

// GOOSE_HOME/build/prog/<stem>-<hash of the root's absolute path>/: where a
// program's C, objects and logs go.
inline string ProgramBuildDir(const string &rootfile, vector<string> definitions = {}) {
    auto abs = AbsolutePath(rootfile);
    #ifdef _WIN32
        for (auto &c : abs) c = (char)tolower((unsigned char)c);   // One directory per file, however spelled.
    #endif
    auto dir = cat(GooseHome(), "/build/prog/", PathStem(rootfile), "-", Hex8(abs));
    if (!definitions.empty()) {
        sort(definitions.begin(), definitions.end());
        string key;
        for (auto &definition : definitions) Append(key, definition.size(), ":", definition);
        Append(dir, "/defines-", Hex8(key));
    }
    return dir;
}

// Runs the toolchain's commands, printing them as -v and --dry-run ask, and
// a failed one with what it printed.
struct Builder {
    const Toolchain &tc;
    const BuildOptions &opts;
    FILE *msgs;

    // The compile flags of both styles: optimization, or debug information
    // and none of it. Defines go into the C itself (main.cpp), never here.
    vector<string> CFlags() const {
        if (tc.style == "msvc") {
            vector<string> f = { "/nologo" };
            if (opts.debug) f.push_back("/Od"), f.push_back("/Zi");
            else f.push_back("/O2");
            return f;
        }
        vector<string> f = opts.debug ? vector<string> { "-O0", "-g" }
                                      : vector<string> { "-O2" };
        if (opts.simd_feedback) {
            f.push_back("-DGS_SIMD_FEEDBACK=1");
            f.push_back("-Rpass=loop-vectorize");
            f.push_back("-Rpass-missed=loop-vectorize");
            f.push_back("-Rpass-analysis=loop-vectorize");
        }
        return f;
    }

    // The system libraries a program links beyond the C library, in the cc
    // style: none on Windows, where they live in the C runtime.
    vector<string> SystemLibs() const {
        #ifdef _WIN32
            return {};
        #else
            if (tc.style == "msvc") return {};
            vector<string> libs = { "-lm", "-pthread" };
            #ifdef __linux__
                // dlopen, for the runtime's dynamic externs: in libdl before
                // glibc 2.34, and in libc since, where the archive left
                // behind is empty.
                libs.push_back("-ldl");
            #endif
            return libs;
        #endif
    }

    // Runs `argv`, `what` being what it does ("compiling the runtime"), with
    // its output kept in `logfile`. False when it failed, after saying so.
    bool Run(const vector<string> &argv, const string &what, const string &logfile) const {
        if (opts.dryrun || opts.verbose) fprintf(msgs, "%s\n", CommandLineText(argv).c_str());
        if (opts.dryrun) return true;
        fflush(msgs);
        ProcessResult r;
        {
            ProgressStep step(what);
            r = RunProcess(argv, "", opts.verbose);
        }
        if (!logfile.empty()) WriteFileMakingDirs(logfile, r.output);
        if (r.started && r.code == 0) {
            if (opts.simd_feedback) {
                string generated;
                for (auto &arg : argv)
                    if (arg.size() >= 2 && arg.substr(arg.size() - 2) == ".c") {
                        LoadFile(arg, generated);
                        break;
                    }
                set<string> loops;
                set<string> sources;
                map<string, string> looplines;
                map<string, string> loopdisplay;
                auto digits = [](const string &s, size_t b, size_t e) {
                    if (b == e) return false;
                    for (auto i = b; i < e; i++) if (!isdigit((uint8_t)s[i])) return false;
                    return true;
                };
                auto unhex = [](string_view in, string &out) {
                    auto nibble = [](char c) {
                        if (c >= '0' && c <= '9') return c - '0';
                        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
                        return -1;
                    };
                    if (in.size() % 2) return false;
                    out.clear();
                    out.reserve(in.size() / 2);
                    for (size_t i = 0; i < in.size(); i += 2) {
                        auto hi = nibble(in[i]), lo = nibble(in[i + 1]);
                        if (hi < 0 || lo < 0) return false;
                        out += (char)((hi << 4) | lo);
                    }
                    return true;
                };
                constexpr string_view metaprefix = "/*goose-simd-loop:";
                bool guarded = false, metadata = false;
                string metasource, metafn;
                for (size_t b = 0; b < generated.size();) {
                    auto e = generated.find('\n', b);
                    if (e == string::npos) e = generated.size();
                    auto p = b;
                    while (p < e && (generated[p] == ' ' || generated[p] == '\t')) p++;
                    auto q = e;
                    while (q > p && (generated[q - 1] == ' ' || generated[q - 1] == '\t' ||
                                     generated[q - 1] == '\r')) q--;
                    string_view text(generated.data() + p, q - p);
                    if (text == "#ifdef GS_SIMD_FEEDBACK") {
                        guarded = true;
                        metadata = false;
                    } else if (guarded && text.substr(0, metaprefix.size()) == metaprefix &&
                               text.size() >= metaprefix.size() + 2 &&
                               text.substr(text.size() - 2) == "*/") {
                        auto body = text.substr(metaprefix.size(),
                                                text.size() - metaprefix.size() - 2);
                        auto sep = body.find(':');
                        metadata = sep != string_view::npos &&
                                   body.find(':', sep + 1) == string_view::npos &&
                                   unhex(body.substr(0, sep), metasource) &&
                                   unhex(body.substr(sep + 1), metafn) &&
                                   !metasource.empty() && !metafn.empty();
                        if (!metadata) guarded = false;
                    } else if (guarded && metadata && text.substr(0, 6) == "#line ") {
                        p += 6;
                        int64_t lineno = 0;
                        auto nb = p;
                        auto ne = p;
                        bool overflow = false;
                        while (p < e && isdigit((uint8_t)generated[p])) {
                            auto digit = generated[p] - '0';
                            if (lineno > (std::numeric_limits<int64_t>::max() - digit) / 10)
                                overflow = true;
                            else if (!overflow) lineno = lineno * 10 + digit;
                            p++;
                        }
                        ne = p;
                        while (p < q && (generated[p] == ' ' || generated[p] == '\t')) p++;
                        if (!overflow && ne > nb && lineno < std::numeric_limits<int64_t>::max() &&
                            p + 2 <= q && generated[p] == '"' && generated[q - 1] == '"') {
                            string file(generated.data() + p + 1, q - p - 2);
                            auto ext = file.size() >= 6 &&
                                       file.compare(file.size() - 6, 6, ".goose") == 0;
                            auto loop = ext ? file.rfind("-loop", file.size() - 6)
                                            : string::npos;
                            auto version = loop == string::npos ? string::npos
                                                                : file.rfind("-v", loop);
                            constexpr string_view prefix = "#goose-simd-";
                            auto element = version == string::npos ? string::npos
                                                                   : file.rfind("-e", version);
                            if (file.compare(0, prefix.size(), prefix) == 0 &&
                                element != string::npos &&
                                digits(file, prefix.size(), element) &&
                                element + 3 == version &&
                                (file[element + 2] == '0' || file[element + 2] == '1') &&
                                digits(file, version + 2, loop) &&
                                digits(file, loop + 5, file.size() - 6)) {
                                loops.insert(file);
                                sources.insert(metasource);
                                loopdisplay[file] = cat(metasource, "#simd-", metafn,
                                                        file.substr(version));
                                // Feedback-only markers close their #ifdef on the
                                // numbered line; the loop is the following line.
                                looplines[file] = std::to_string(lineno + 1);
                            }
                        }
                        guarded = metadata = false;
                    } else {
                        guarded = metadata = false;
                    }
                    b = e < generated.size() ? e + 1 : generated.size();
                }
                set<string> explained;
                set<string> vectorized;
                // Clang brackets an inlined-loop remark with notes naming the
                // logical #line file: one before the primary diagnostic and
                // one after it. A note on just one side can instead belong to
                // the neighbouring diagnostic. Correlate only the intersection
                // of the two boundaries so an unrelated remark cannot inherit
                // a loop merely because it was printed immediately before it.
                struct SimdRemark {
                    string text;
                    map<string, string> direct;
                };
                vector<SimdRemark> remarks;
                vector<map<string, string>> boundaries(1);
                auto diagnostic = [&](const string &line, string_view kind,
                                      size_t &tag, string &file, string &location) {
                    auto marker = cat(": ", kind, ":");
                    tag = line.find(marker);
                    if (tag == string::npos || !tag) return false;
                    auto col = line.rfind(':', tag - 1);
                    auto row = col == string::npos || !col ? string::npos
                                                            : line.rfind(':', col - 1);
                    if (row == string::npos || !digits(line, row + 1, col) ||
                        !digits(line, col + 1, tag)) return false;
                    file = line.substr(0, row);
                    location = line.substr(0, tag);
                    return true;
                };
                auto report = [&](const string &loop, const string &location,
                                  const string &remark) {
                    fprintf(msgs, "simd feedback: %s: %s\n", location.c_str(), remark.c_str());
                    explained.insert(loop);
                    if (remark.find("[-Rpass=loop-vectorize]") != string::npos)
                        vectorized.insert(loop);
                };
                for (size_t b = 0; b < r.output.size();) {
                    auto e = r.output.find('\n', b);
                    auto line = r.output.substr(b, e == string::npos ? string::npos : e - b);
                    const string lostmsg = "could not determine the original source location for ";
                    size_t tag = 0;
                    string file, location;
                    if (diagnostic(line, "remark", tag, file, location)) {
                        SimdRemark remark { line.substr(tag + 2), {} };
                        for (auto &loop : loops) {
                            if (file != loop || sources.count(file)) continue;
                            remark.direct[loop] = loopdisplay[loop] +
                                                  location.substr(file.size());
                            break;
                        }
                        remarks.push_back(std::move(remark));
                        boundaries.emplace_back();
                    } else if (diagnostic(line, "note", tag, file, location)) {
                        auto body = tag + 8;
                        if (line.compare(body, lostmsg.size(), lostmsg) == 0) {
                            auto at = line.substr(body + lostmsg.size());
                            for (auto &loop : loops) {
                                if (at.size() <= loop.size() || at[loop.size()] != ':' ||
                                    at.compare(0, loop.size(), loop) != 0) continue;
                                auto scope = loop;
                                auto suffix = scope.rfind("-loop", scope.size() - 6);
                                scope.replace(suffix, string::npos, ".goose");
                                if (!sources.count(file) && file != scope) continue;
                                boundaries.back()[loop] = loopdisplay[loop] +
                                                          at.substr(loop.size());
                                break;
                            }
                        }
                    }
                    if (e == string::npos) break;
                    b = e + 1;
                }
                vector<map<string, string>> assigned;
                assigned.reserve(remarks.size());
                for (size_t i = 0; i < remarks.size(); i++) {
                    assigned.push_back(remarks[i].direct);
                    for (auto &[loop, location] : boundaries[i])
                        if (boundaries[i + 1].count(loop)) assigned[i][loop] = location;
                }
                // The first/last primary may have no outer note. Attribute a
                // loop at that edge only when the neighbouring primary already
                // accounts for every other possibility on the shared boundary.
                if (remarks.size() == 1) {
                    for (auto &[loop, location] : boundaries[0]) assigned[0][loop] = location;
                    for (auto &[loop, location] : boundaries[1]) assigned[0][loop] = location;
                } else if (!remarks.empty()) {
                    for (auto &[loop, location] : boundaries[1])
                        if (!assigned[1].count(loop)) assigned[0][loop] = location;
                    auto last = remarks.size() - 1;
                    for (auto &[loop, location] : boundaries[last])
                        if (!assigned[last - 1].count(loop)) assigned[last][loop] = location;
                }
                for (size_t i = 0; i < remarks.size(); i++)
                    for (auto &[loop, location] : assigned[i])
                        report(loop, location, remarks[i].text);
                for (auto &loop : loops) if (!vectorized.count(loop))
                    fprintf(msgs, "simd feedback: %s:%s: missed: %s\n",
                            loopdisplay[loop].c_str(),
                            looplines[loop].c_str(), explained.count(loop)
                                ? "compiler supplied no positive vectorization remark; see remarks above"
                                : "compiler supplied no loop-vectorize reason");
            }
            return true;
        }
        auto msg = cat(what, " failed", r.started ? cat(" (exit ", r.code, ")") : string(), ":\n    ",
                       CommandLineText(argv), "\n");
        if (!opts.verbose) msg += r.output;
        if (!logfile.empty())
            Append(msg, msg.back() == '\n' ? "" : "\n", "(the output is in ", logfile, ")");
        ProgressPrint(msg);
        return false;
    }

    // A system library by name, as the style's linker takes it.
    string LibFlag(const string &lib) const {
        return tc.style == "msvc" ? cat(lib, ".lib") : cat("-l", lib);
    }

    // Compiles the C file `src` to the object `obj`, with `extra` flags
    // (a package's includes and defines) after the usual ones.
    bool CompileObject(const string &src, const string &obj, const string &what,
                       const string &logfile, const vector<string> &extra = {}) const {
        vector<string> argv = { tc.cc };
        for (auto &f : CFlags()) argv.push_back(f);
        for (auto &f : extra) argv.push_back(f);
        if (tc.style == "msvc") {
            argv.push_back("/c");
            argv.push_back(src);
            argv.push_back(cat("/Fo:", obj));
            if (opts.debug) argv.push_back(cat("/Fd:", obj, ".pdb"));
        } else {
            argv.push_back("-c");
            argv.push_back(src);
            argv.push_back("-o");
            argv.push_back(obj);
        }
        return Run(argv, what, logfile);
    }

    // Links `objects` and the system libraries `libs` (LibFlag spellings)
    // into the shared library `out`, with `builddir` taking the
    // intermediates: a package's JIT library.
    bool LinkShared(const vector<string> &objects, const vector<string> &libs, const string &out,
                    const string &builddir, const string &logfile, const string &what) const {
        vector<string> argv = { tc.cc };
        if (tc.style == "msvc") {
            argv.push_back("/nologo");
            argv.push_back("/LD");
            argv.push_back(cat("/Fe:", out));
            argv.push_back(cat("/Fo:", builddir, "\\"));
            for (auto &o : objects) argv.push_back(o);
            for (auto &l : libs) argv.push_back(l);
        } else {
            argv.push_back("-shared");
            for (auto &o : objects) argv.push_back(o);
            argv.push_back("-o");
            argv.push_back(out);
            for (auto &l : libs) argv.push_back(l);
            for (auto &l : SystemLibs()) argv.push_back(l);
        }
        return Run(argv, what, logfile);
    }

    // Compiles `src` and links it with `objects` and the response files
    // `rsps` into `exe`, with `builddir` taking the intermediates.
    vector<string> LinkCommand(const string &src, const vector<string> &objects,
                               const vector<string> &rsps, const string &exe,
                               const string &builddir, const vector<string> &extra = {}) const {
        vector<string> argv = { tc.cc };
        for (auto &f : CFlags()) argv.push_back(f);
        for (auto &f : extra) argv.push_back(f);
        if (tc.style == "msvc") {
            argv.push_back(cat("/Fe:", exe));
            argv.push_back(cat("/Fo:", builddir, "\\"));
            if (opts.debug) argv.push_back(cat("/Fd:", builddir, "\\", PathStem(exe), ".pdb"));
            argv.push_back(src);
            for (auto &o : objects) argv.push_back(o);
            for (auto &r : rsps) argv.push_back(cat("@", r));
        } else {
            argv.push_back(src);
            for (auto &o : objects) argv.push_back(o);
            argv.push_back("-o");
            argv.push_back(exe);
            for (auto &r : rsps) argv.push_back(cat("@", r));
            for (auto &l : SystemLibs()) argv.push_back(l);
        }
        return argv;
    }

    bool Link(const string &src, const vector<string> &objects, const vector<string> &rsps,
              const string &exe, const string &builddir, const string &logfile,
              const vector<string> &extra = {}) const {
        return Run(LinkCommand(src, objects, rsps, exe, builddir, extra), cat("building ", exe), logfile);
    }
};

// The runtime object for this toolchain and configuration, compiled from
// `goose --emit-runtime`'s C on first use: GOOSE_HOME/build/runtime/<runtime
// hash>/<toolchain id>-<config>/goose_runtime.o. "" when it could not be
// built, after the builder said why.
inline string RuntimeObject(const Builder &b, const std::function<BuildInputStamp(const string &)> &benchinputs = {}) {
    auto dir = cat(GooseHome(), "/build/runtime/", RuntimeVersion(), "/", b.tc.id, "-",
                   b.opts.debug ? "debug" : "release");
    auto obj = cat(dir, "/goose_runtime.", b.tc.style == "msvc" ? "obj" : "o");
    auto src = cat(dir, "/goose_runtime.c");
    if (!benchinputs && PathExists(obj) && !b.opts.dryrun) return obj;
    auto log = cat(dir, "/cc.log");
    if (b.opts.dryrun) {
        b.CompileObject(src, obj, "compiling the runtime", log);
        return obj;
    }
    std::error_code ec;
    filesystem::create_directories(filesystem::path(dir), ec);
    if (ec) throw CompileError { cat("cannot create ", dir, ": ", ec.message()) };
    // Every first build shares these paths. Wait before writing the source
    // or invoking the compiler, then recheck what the previous builder left.
    FileLock lock(cat(dir, "/build.lock"), "waiting for another goose compiling the runtime");
    if (!benchinputs && PathExists(obj)) return obj;
    if (!WriteFileIfChanged(src, RuntimeObjectSource()))
        throw CompileError { cat("cannot write ", src) };
    auto stampfile = cat(dir, "/goose-bench-inputs.txt");
    BuildInputStamp captured;
    if (benchinputs) {
        captured = benchinputs(src);
        string previous;
        if (PathExists(obj) && LoadFile(stampfile, previous) && previous == captured.content) return obj;
        // Missing stamps include caches built before content validation.
        // Invalidate before rebuilding, including an interrupted rebuild.
        filesystem::remove(stampfile, ec);
        if (ec) throw CompileError { cat("cannot remove ", stampfile, ": ", ec.message()) };
    }
    ProgressStep step(cat("compiling the runtime for ", b.tc.desc), true);
    // A failed or interrupted compiler may leave a partial object. Only a
    // successful compile publishes the name readers use, by atomic rename.
    auto tmp = cat(dir, "/goose_runtime.tmp.", b.tc.style == "msvc" ? "obj" : "o");
    filesystem::remove(filesystem::path(tmp), ec);
    if (ec) throw CompileError { cat("cannot remove ", tmp, ": ", ec.message()) };
    if (!b.CompileObject(src, tmp, "compiling the runtime", log)) return "";
    if (benchinputs) captured.verify();
    ec = RenamePath(tmp, obj);
    if (ec) throw CompileError { cat("cannot publish ", obj, ": ", ec.message()) };
    if (benchinputs && !WriteFileIfChanged(stampfile, captured.content))
        throw CompileError { cat("cannot write ", stampfile) };
    return obj;
}

// What `goose build` does once the compiler has written the program's C to
// `cfile` in `builddir`: finds the runtime object for the toolchain `tc`,
// which built the native parts whose response files are `nativersps`
// (native.h and builtin.h, found by the caller) in link order, a package's
// before the packages it requires and the program's own C first of all, and
// links the executable, named by -o, the program's sidecar (`output`) or the
// root file. The exit code.
inline int BuildExecutable(const string &rootfile, const string &cfile, const string &builddir,
                           const Toolchain &tc, const BuildOptions &opts, FILE *msgs,
                           const vector<string> &nativersps, const string &output) {
    Builder b { tc, opts, msgs };
    vector<string> objects;
    if (!opts.standalone) {
        auto obj = RuntimeObject(b);
        if (obj.empty()) return 1;
        objects.push_back(obj);
    }
    auto exe = opts.exe;
    if (exe.empty()) {
        exe = cat(DirOf(rootfile), output.empty() ? PathStem(rootfile) : output);
        #ifdef _WIN32
            if (exe.size() < 4 || exe.compare(exe.size() - 4, 4, ".exe") != 0) exe += ".exe";
        #endif
    }
    if (!opts.dryrun) {
        std::error_code ec;
        auto exedirpath = filesystem::path(exe).parent_path();
        if (!exedirpath.empty()) filesystem::create_directories(exedirpath, ec);
    }
    if (!b.Link(cfile, objects, nativersps, exe, builddir, cat(builddir, "/cc.log"))) return 1;
    if (!opts.dryrun) fprintf(msgs, "built %s\n", exe.c_str());
    return 0;
}

}  // namespace goose
