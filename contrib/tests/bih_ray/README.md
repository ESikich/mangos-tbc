# BIH ray traversal regression

From a source checkout, run:

```sh
python3 contrib/tests/bih_ray/run.py
```

Requires Linux, Python 3, a C++20 compiler (`CXX`, default `g++`), AddressSanitizer,
and Boost headers required by bundled G3D. No server, database, extracted maps,
downloaded dependencies, or client assets are required. Temporary executables
are removed automatically.

The fixture includes the checkout's actual `BIH.h` and compiles its bundled
G3D ray/vector implementation. A two-node tree preserves the missing-child
self-reference from a captured crash; the NaN payload and direction reproduce
the invalid traversal. An explicitly cyclic fixture separately exercises the
stack bound. These are synthetic tree fixtures, not retail geometry files.

Controls check ordinary finite rays, positive-infinite maximum distance (used
by indoor queries), zero distance, and unchanged hit distances. Invalid origin,
direction and distance cases must return without reaching the callback.

To verify the original failure with a separate unpatched checkout:

```sh
python3 contrib/tests/bih_ray/run.py \
    --source-root /path/to/unpatched/checkout --expect-unfixed
```

Only the specific sanitizer stack-buffer-overflow signature counts as an
expected failure; crashes and timeouts otherwise fail the test. The captured
case is repeated three times. This does not replace a full client indoor
dismount test or a collision-map integrity audit. A stack-bound abort prevents
memory corruption but can leave the caller with an incomplete collision result.

Related reports: [3913](https://github.com/cmangos/issues/issues/3913) and
[3956](https://github.com/cmangos/issues/issues/3956).
