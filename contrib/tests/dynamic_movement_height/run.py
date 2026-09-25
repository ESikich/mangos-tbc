#!/usr/bin/env python3
"""Exercise the actual MOVE_DYNAMIC height initialization in an isolated fixture."""
import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path,
                        default=Path(__file__).resolve().parents[3])
    parser.add_argument("--expect-unfixed", action="store_true")
    args = parser.parse_args()
    source = (args.source_root / "src/game/DBScripts/ScriptMgr.cpp").read_text()
    section = source.rsplit("case SCRIPT_COMMAND_MOVE_DYNAMIC:", 1)[1]
    section = section.split("case SCRIPT_COMMAND_SEND_MAIL:", 1)[0]
    declaration = re.search(r"float x, y, z[^;]*;", section).group()
    branch = section.split(
        "if (m_script->data_flags & SCRIPT_FLAG_COMMAND_ADDITIONAL) // no bounding radius"
    )[1].split("{", 1)[1].split("}", 1)[0]
    fixture = r'''
#include <cstdio>
#include <stdexcept>
struct Target
{
    float height;
    float GetPositionX() const { return 10.f; }
    float GetPositionY() const { return 20.f; }
    float GetPositionZ() const { return height; }
    void* GetMap() const { return nullptr; }
    float GetAngle(void*) const { return 0.f; }
    void GetNearPoint2dAt(float px, float py, float& x, float& y, float, float) const
    {
        x = px + 1;
        y = py + 2;
    }
};
struct Source
{
    float expected;
    int calls = 0;
    __attribute__((noinline)) void UpdateAllowedPositionZ(float x, float y, float& z, void*)
    {
        ++calls;
        if (x != 11.f || y != 22.f)
            throw std::runtime_error("unexpected XY");
        if (z != expected)
            throw std::runtime_error("target height not initialized");
        z += 0.5f;
    }
};
struct Script { struct { float fixedDist = 1.f; } moveDynamic; };
int main()
{
    try
    {
        for (float height : {37.5f, -12.25f, 0.f})
        {
            Target target{height}; Target* pTarget = &target;
            Source object{height}; Source* source = &object;
            Script script; Script* m_script = &script;
            DECLARATION
            BRANCH
            if (source->calls != 1 || z != height + 0.5f)
                throw std::runtime_error("height correction not preserved");
        }
        std::puts("PASS: target heights initialized and corrected heights preserved");
    }
    catch (const std::exception& error)
    {
        std::puts(error.what());
        return 1;
    }
}
'''.replace("DECLARATION", declaration).replace("BRANCH", branch)
    with tempfile.TemporaryDirectory(prefix="cmangos-movement-") as directory:
        cpp = Path(directory) / "movement.cpp"
        binary = Path(directory) / "movement"
        cpp.write_text(fixture)
        command = shlex.split(os.environ.get("CXX", "g++"))
        command += ["-std=c++20", "-O3", "-DNDEBUG",
                    "-ftrivial-auto-var-init=pattern", str(cpp), "-o", str(binary)]
        subprocess.run(command, check=True)
        result = subprocess.run([str(binary)], text=True, capture_output=True, timeout=10)
        if args.expect_unfixed:
            passed = result.returncode == 1 and "target height not initialized" in result.stdout
        else:
            passed = result.returncode == 0 and "PASS:" in result.stdout
        print(result.stdout.strip())
        if not passed:
            raise SystemExit("FAIL: unexpected result")
        if args.expect_unfixed:
            print("PASS: reproduced the missing height assignment")


if __name__ == "__main__":
    main()
