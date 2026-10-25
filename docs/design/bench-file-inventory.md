# Benchmark Goose File Inventory

Printed results are the lines emitted by running each file with `goose++ run` at its checked-in benchmark size.

| File | Lines | Defines `fn main` | `BENCH` constant(s) | Printed result (lines in order) |
|---|---:|:---:|---|---|
| `bintrees.goose` | 55 | Yes | `MAXDEPTH = 17` | `524287<br>131072<br>4<br>4063232<br>32768<br>6<br>4161536<br>8192<br>8<br>4186112<br>2048<br>10<br>4192256<br>512<br>12<br>4193792<br>128<br>14<br>4194176<br>32<br>16<br>4194272<br>262143` |
| `blur.goose` | 47 | Yes | `W = 2048` | `2048<br>502239988` |
| `blur_assert.goose` | 45 | Yes | `W = 2048` | `2048<br>502239988` |
| `blur_rows.goose` | 48 | Yes | `W = 2048` | `2048<br>502239988` |
| `calc.goose` | 199 | Yes | `N = 250000` | `10356411<br>4215138<br>162282<br>3530<br>38369<br>35786<br>10033<br>1262248511348321861` |
| `calc_noerr.goose` | 174 | Yes | `N = 250000` | `10542205<br>4634484<br>250000<br>0<br>0<br>0<br>0<br>7260133884543341186` |
| `calc_noparen.goose` | 200 | Yes | `N = 250000` | `10356411<br>3903633<br>162282<br>3530<br>38369<br>35786<br>10033<br>1262248511348321861` |
| `calc_slices.goose` | 190 | Yes | `N = 250000` | `10356411<br>4215138<br>162282<br>3530<br>38369<br>35786<br>10033<br>1262248511348321861` |
| `graph.goose` | 79 | Yes | `V = 1000000` | `9000000<br>27635866` |
| `graph_csr.goose` | 83 | Yes | `V = 1000000` | `9000000<br>27635866` |
| `interp.goose` | 52 | Yes | `DEPTH = 20` | `294997<br>950682` |
| `lru.goose` | 168 | Yes | `N = 8000000` | `4937489<br>2561689<br>329505<br>1000000<br>1009107182135619685<br>501925078` |
| `lru_indices.goose` | 151 | Yes | `N = 8000000` | `4937489<br>2561689<br>329505<br>1000000<br>1009107182135619685<br>501925078` |
| `lru_nonopt.goose` | 146 | Yes | `N = 8000000` | `4937489<br>2561689<br>329505<br>1000000<br>1009107182135619685<br>501925078` |
| `particles.goose` | 53 | Yes | `N = 200000` | `200000<br>3866765125` |
| `particles_scalar.goose` | 52 | Yes | `N = 200000` | `200000<br>3866765125` |
| `push.goose` | 31 | Yes | `N = 4000000` | `4000000<br>62500<br>1999475402287<br>3000138` |
| `push_ref.goose` | 42 | Yes | `N = 4000000` | `4000000<br>62500<br>1999719066513<br>3000169` |
| `records_fixed.goose` | 63 | Yes | `N = 2000000` | `2000000<br>350419807120` |
| `records_var.goose` | 68 | Yes | `N = 2000000` | `2000000<br>350419807120` |
| `respond.goose` | 136 | Yes | `N = 400000` | `400000<br>91800236<br>8685297199210497210` |
| `respond_stream.goose` | 98 | Yes | `N = 400000` | `400000<br>91800236<br>8685297199210497210` |
| `rng.goose` | 14 | No | — | — |
| `scene.goose` | 105 | Yes | `DEPTH = 13` | `101800<br>3009077` |
| `sexp.goose` | 146 | Yes | `N = 200000` | `95891859<br>15219545<br>200000<br>0<br>1095074941564` |
| `strlist.goose` | 38 | Yes | `N = 400000` | `400000<br>368751732` |
| `sum.goose` | 25 | Yes | `N = 4000000` | `4000000<br>15987891712` |
| `tree.goose` | 50 | Yes | `DEPTH = 20` | `2097151<br>8377899684` |
| `words.goose` | 71 | Yes | `N = 2000000` | `2000000<br>146190<br>236020268` |
| `words_dictionary.goose` | 47 | Yes | `N = 2000000` | `2000000<br>146190<br>236020268` |
