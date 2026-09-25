#include "BIH.h"
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

// This fixture uses BIH's real node encoding for a missing lower child.
// The captured node 861 referred to itself; here it is relocated to index 0.
class Fixture : public BIH
{
public:
    explicit Fixture(bool invalidCycle = false)
    {
        bounds = AABox(Vector3(-100, -100, -100), Vector3(100, 100, 100));
        tree = {uint32(2u << 30),
                floatToRawIntBits(invalidCycle ? 100.f : -std::numeric_limits<float>::infinity()),
                invalidCycle ? floatToRawIntBits(0.f) : 0x41f82005u,
                uint32(3u << 30), 1, 0};
        objects = {42};
    }
};

struct Callback
{
    unsigned calls = 0;
    bool operator()(const Ray&, uint32 object, float& distance, bool, bool)
    {
        if (object != 42)
            throw std::runtime_error("wrong object index");
        ++calls;
        distance = 1.f;
        return true;
    }
};

float CapturedNaN()
{
    uint32 bits = 0xfff47290u;
    return intBitsToFloat(bits);
}

void Require(bool condition, const char* message)
{
    if (!condition)
        throw std::runtime_error(message);
}

void Run(const std::string& mode)
{
    const float nan = CapturedNaN(), inf = std::numeric_limits<float>::infinity();
    Vector3 origin(0, 0, 40), direction(-0.0174524039f, 0.9979826808f, 0.0610392876f);
    float distance = 100.f;
    bool expectNoHit = false, cycle = false;
    if (mode == "captured")
    {
        origin = Vector3(nan, nan, nan);
        expectNoHit = true;
    }
    else if (mode == "nan-height")
    {
        origin.z = nan;
        expectNoHit = true;
    }
    else if (mode == "infinite-origin")
    {
        origin.z = inf;
        expectNoHit = true;
    }
    else if (mode == "nan-direction")
    {
        direction.z = nan;
        expectNoHit = true;
    }
    else if (mode == "infinite-direction")
    {
        direction.z = inf;
        expectNoHit = true;
    }
    else if (mode == "zero-distance")
    {
        origin = Vector3(0, 0, 200);
        direction = Vector3(0, 0, -1);
        distance = 0;
        expectNoHit = true;
    }
    else if (mode == "negative-infinite-distance")
    {
        distance = -inf;
        expectNoHit = true;
    }
    else if (mode == "nan-distance")
    {
        distance = nan;
        expectNoHit = true;
    }
    else if (mode == "negative-distance")
    {
        distance = -1;
        expectNoHit = true;
    }
    else if (mode == "infinite-distance")
    {
        distance = inf;
    }
    else if (mode == "stack-limit")
    {
        cycle = true;
        origin = Vector3(0, 0, 0);
        direction = Vector3(0, 0, 1);
    }
    else if (mode != "finite")
        throw std::runtime_error("unknown test");
    Fixture tree(cycle);
    Callback callback;
    Ray ray = Ray::fromOriginAndDirection(origin, direction);
    tree.intersectRay(ray, callback, distance, true, false);
    if (expectNoHit || cycle)
        Require(callback.calls == 0, "unexpected geometry callback");
    else
    {
        Require(callback.calls == 1, "valid ray did not reach geometry");
        Require(distance == 1.f, "valid hit distance changed");
    }
}

int main(int argc, char** argv)
{
    if (argc != 2)
        return 2;
    try
    {
        Run(argv[1]);
        std::cout << "PASS " << argv[1] << "\n";
        return 0;
    }
    catch (const std::exception& e)
    {
        std::cerr << e.what() << "\n";
        return 1;
    }
}
