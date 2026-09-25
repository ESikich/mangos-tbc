#!/usr/bin/env python3
"""Compile the checkout's native BIH implementation and reproduce invalid-ray overflow."""
import argparse
import os
from pathlib import Path
import shlex
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path,
                        default=Path(__file__).resolve().parents[3])
    parser.add_argument("--expect-unfixed", action="store_true")
    args = parser.parse_args()
    root = args.source_root.resolve()
    here = Path(__file__).resolve().parent
    g3d = root / "dep/g3dlite"
    environment = dict(os.environ)
    environment["ASAN_OPTIONS"] = (
        "detect_leaks=0:abort_on_error=0:exitcode=86:disable_coredump=1"
    )
    controls = ["finite", "infinite-distance", "zero-distance"]
    failures = ["captured", "nan-height", "stack-limit"]
    modes = controls + failures
    if not args.expect_unfixed:
        modes += ["infinite-origin", "nan-direction", "infinite-direction",
                  "nan-distance", "negative-distance", "negative-infinite-distance"]
    with tempfile.TemporaryDirectory(prefix="cmangos-bih-") as directory:
        binary = Path(directory) / "bih"
        command = shlex.split(os.environ.get("CXX", "g++"))
        command += ["-std=c++20", "-DNDEBUG", "-O1", "-g", "-fsanitize=address",
                    "-fno-omit-frame-pointer", "-fno-pie", "-no-pie",
                    "-ffunction-sections", "-fdata-sections", "-Wl,--gc-sections",
                    "-I" + str(root / "src/game/vmap"), "-I" + str(g3d),
                    "-I" + str(root / "src/shared"), str(here / "collision_test.cpp"),
                    str(g3d / "Ray.cpp"), str(g3d / "Vector3.cpp"),
                    str(g3d / "g3dmath.cpp"), "-o", str(binary)]
        subprocess.run(command, check=True)
        count = 0
        for mode in modes:
            for _ in range(3 if mode == "captured" else 1):
                result = subprocess.run([str(binary), mode], text=True,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        timeout=10, env=environment)
                if args.expect_unfixed and mode in failures:
                    passed = (result.returncode == 86
                              and "AddressSanitizer: stack-buffer-overflow" in result.stdout
                              and "intersectRay" in result.stdout)
                    description = "expected sanitizer overflow"
                else:
                    passed = result.returncode == 0 and "PASS " + mode in result.stdout
                    description = "clean exit"
                print(f"{'PASS' if passed else 'FAIL'} {mode}: {description}")
                if not passed:
                    print(result.stdout)
                    raise SystemExit(1)
                count += 1
        print(f"All {count} checks passed.")


if __name__ == "__main__":
    main()
