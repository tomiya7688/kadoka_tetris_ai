# C++ Memory Safety Checks

The `cpp-memory-safety` CI job builds and runs the C++ Core, Runtime, benchmark, and CTest targets with AddressSanitizer, LeakSanitizer, and UndefinedBehaviorSanitizer on Ubuntu.

```powershell
cmake -S . -B build-cpp-sanitized -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON -DKADOKA_ENABLE_SANITIZERS=ON
cmake --build build-cpp-sanitized --config Debug
ctest --test-dir build-cpp-sanitized -C Debug --output-on-failure
```

AddressSanitizer reports out-of-bounds access, use-after-free, double-free, and invalid free. LeakSanitizer checks for unreachable leaked allocations when each test process exits; CI sets its leak exit code to 23 so any detected leak fails the test job. UBSan makes supported undefined behavior fail the same job. Reachable process-lifetime allocations are treated as still reachable, so the check cannot decide whether such caches should have been released earlier.

The CI also compiles and runs a tiny intentional-leak probe and requires LeakSanitizer's report and nonzero exit code. This verifies that leak detection is active rather than merely requested by environment variables.

These are dynamic checks: they cover paths exercised by CTest and cannot prove that every possible input or path is memory-safe. Keep ownership RAII-based (`std::vector`, `std::unique_ptr`, and scoped values) so ordinary cleanup does not depend on manually paired `new`/`delete` or `malloc`/`free` calls.
