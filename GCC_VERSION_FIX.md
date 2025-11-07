# GCC Version Detection Fix - November 7, 2025

## Summary

Fixed GCC version detection in `homebrew_manager.py` to correctly identify GCC 15 instead of incorrectly reporting GCC 11.

## Problem

The GCC version detection logic was using `head -1` which picked up the first file in alphabetical order:
- Found: `gcc-11` (which is actually a symlink to gcc-15)
- Expected: `gcc-15` (the actual installed version)
- Result: Setup script reported "Found GCC version: 11" when it should report "15"

## Root Cause

```bash
# Old command picked first result alphabetically:
ls /home/linuxbrew/.linuxbrew/bin/gcc-* | grep -E 'gcc-[0-9]+$' | head -1
# Returns: /home/linuxbrew/.linuxbrew/bin/gcc-11 (symlink)
```

The directory listing shows:
```
gcc-11 -> gcc-15  (symlink)
gcc-12 -> gcc-15  (symlink)
gcc-13 -> gcc-15  (symlink)
gcc-14 -> gcc-15  (symlink)
gcc-15 -> ../Cellar/gcc/15.2.0/bin/gcc-15  (actual binary)
```

## Solution

Updated detection to:
1. **Prefer Cellar paths** (actual binaries) over symlinks
2. **Use version sorting** (`sort -V`) to get numerically highest version
3. **Use `tail -1`** instead of `head -1` to get the highest version

```python
# New logic - tries Cellar path first:
result = self._run_command(
    f"ls -l {self.homebrew_bin}/gcc-* 2>/dev/null | grep Cellar | grep -E 'gcc-[0-9]+$' | tail -1",
    check=False
)

# Fallback - use version sort:
if result.returncode != 0 or not result.stdout.strip():
    result = self._run_command(
        f"ls {self.homebrew_bin}/gcc-* 2>/dev/null | grep -E 'gcc-[0-9]+$' | sort -V | tail -1",
        check=False
    )
```

## Verification

### Before Fix
```
Found GCC version: 11
✓ Created compiler symlinks:
  gcc/g++/gfortran -> gcc-11 (latest from Homebrew)
  gcc-11/g++-11/etc -> gcc-11 (compatibility for PGAS libraries)
```

### After Fix
```
Found GCC version: 15
✓ Created compiler symlinks:
  gcc/g++/gfortran -> gcc-15 (latest from Homebrew)
  gcc-11/g++-11/etc -> gcc-15 (compatibility for PGAS libraries)
```

## Regression Testing Results

All 9 regression tests **PASSED** ✅

### Test 1: GCC Version Detection
```bash
$ /home/linuxbrew/.linuxbrew/bin/gcc --version
gcc (Homebrew GCC 15.2.0) 15.2.0
✅ PASS
```

### Test 2: GCC-11 Compatibility Symlink
```bash
$ /home/linuxbrew/.linuxbrew/bin/gcc-11 --version
gcc-11 (Homebrew GCC 15.2.0) 15.2.0
✅ PASS - Compatibility symlink works
```

### Test 3: All Compatibility Symlinks
```bash
$ for v in 11 12 13 14; do readlink /home/linuxbrew/.linuxbrew/bin/gcc-$v; done
/home/linuxbrew/.linuxbrew/bin/gcc-15
/home/linuxbrew/.linuxbrew/bin/gcc-15
/home/linuxbrew/.linuxbrew/bin/gcc-15
/home/linuxbrew/.linuxbrew/bin/gcc-15
✅ PASS - All point to gcc-15
```

### Test 4: Benchmark Run Script Generation
```bash
$ ls -lh /home/muyiwa/cluster_build_sources/benchmarks/run_benchmarks.sh
-rwxr-xr-x 1 muyiwa muyiwa 4.3K Nov  7 08:45 run_benchmarks.sh
✅ PASS
```

### Test 5: pdsh Cluster Connectivity
```bash
$ pdsh -w 192.168.1.139,192.168.1.96 hostname
192.168.1.96: oluubuntul1
192.168.1.139: muyiwadroexperiments
✅ PASS
```

### Test 6: OpenMPI Installation
```bash
$ mpirun --version
mpirun (Open MPI) 5.0.8
✅ PASS
```

### Test 7: C++23 Compilation with GCC-15
```bash
$ /home/linuxbrew/.linuxbrew/bin/g++-15 -std=c++23 test.cpp -o test
$ ./test
C++ version: 202302
GCC version: 15.2.0
C++20 Concepts: supported
✅ PASS - Can compile C++23 programs
```

### Test 8: C++23 via GCC-11 Compatibility Symlink
```bash
$ /home/linuxbrew/.linuxbrew/bin/g++-11 -std=c++23 test.cpp -o test
$ ./test
C++ version: 202302
GCC version: 15.2.0
✅ PASS - Compatibility symlink works for compilation
```

### Test 9: Full Cluster Setup Execution
```bash
$ uv run python cluster_setup.py --config cluster_config_actual.yaml --password
...
Found GCC version: 15
✓ Created compiler symlinks:
  gcc/g++/gfortran -> gcc-15 (latest from Homebrew)
  gcc-11/g++-11/etc -> gcc-15 (compatibility for PGAS libraries)
...
✓ LOCAL NODE SETUP COMPLETED SUCCESSFULLY
✅ PASS - Setup completes with correct version detection
```

## Impact

### Positive Changes
- ✅ Correct version reporting (15 instead of 11)
- ✅ Better detection logic that handles future GCC versions
- ✅ More robust fallback mechanism
- ✅ All existing functionality preserved

### No Breaking Changes
- ✅ All symlinks still work correctly
- ✅ Backward compatibility maintained (gcc-11 symlink still exists)
- ✅ PGAS libraries can still find gcc-11 if they need it
- ✅ All benchmarks still generate correctly

## Files Modified

```
cluster_modules/homebrew_manager.py
  - Updated create_gcc_symlinks() method
  - Lines 152-164: New detection logic
  - Added fallback mechanism
```

## Cluster Status After Fix

**Cluster Configuration:**
- Master: 192.168.1.147 (Ubuntu WSL2) - 32 threads
- Worker 1: 192.168.1.139 (Ubuntu) - 16 threads
- Worker 2: 192.168.1.96 (Ubuntu) - 16 threads

**Verified Working:**
- ✅ GCC 15.2.0 correctly detected
- ✅ All symlinks properly configured
- ✅ pdsh connectivity to all nodes
- ✅ OpenMPI 5.0.8
- ✅ UPC++ 2025.10.0
- ✅ Benchmarks generated
- ✅ run_benchmarks.sh script created

## Git Commit

**Commit:** 17d36f9
**Message:** fix: Correct GCC version detection to find gcc-15 instead of gcc-11
**Branch:** master
**Status:** ✅ Pushed to origin/master

## Related Issues

This fix addresses the issue reported where the setup was showing:
> "Found GCC version: 11"

When it should have shown:
> "Found GCC version: 15"

The actual GCC version installed is 15.2.0, and the fix ensures this is correctly detected.

## Known Limitations

⚠️ **Note:** GCC 15.2.0 has compatibility issues with older system glibc versions. This is a known upstream issue and NOT related to this fix. Workaround: Use system GCC 14.2.0 for compilation if needed.

## Author

Olumuyiwa Oluwasanmi
Date: November 7, 2025
Commit: 17d36f9
