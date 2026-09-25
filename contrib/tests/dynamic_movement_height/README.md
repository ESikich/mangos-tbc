# Dynamic movement destination height regression

From a source checkout, run:

```sh
python3 contrib/tests/dynamic_movement_height/run.py
```

Requires Python 3 and GCC 12+ (or a compatible compiler selected with `CXX`)
supporting `-ftrivial-auto-var-init=pattern`. No server, database or client data
is required. Build artifacts live in a temporary directory and are removed.

The runner extracts the destination declaration and actual additional-flag,
zero-max-distance branch from `ScriptMgr.cpp`. A fixture records the height
passed to `UpdateAllowedPositionZ`, checking positive, negative and zero target
heights and retention of the corrected output. Compiler initialization exposes
the old missing assignment deterministically; it is not used in production.

To demonstrate the original failure using another, unpatched checkout:

```sh
python3 contrib/tests/dynamic_movement_height/run.py \
    --source-root /path/to/unpatched/checkout --expect-unfixed
```

This tests the extracted script branch, not full script dispatch or terrain.
