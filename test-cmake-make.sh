#!/bin/bash
# test-cmake-make.sh - Test CMake Unix Makefiles build for iPlug2
#
# Tests that the CMake build system correctly generates Makefiles
# and all plugin formats build successfully.
#
# Usage: ./test-cmake-make.sh [--clean]
#   --clean: Remove build directories before and after tests

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IPLUG2_DIR="$SCRIPT_DIR/iPlug2"

# Test counters
PASSED=0
FAILED=0
FAILED_TESTS=()

# Options
CLEAN_BUILDS=false
if [[ "$1" == "--clean" ]]; then
  CLEAN_BUILDS=true
fi

# =============================================================================
# Output helpers
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

pass() {
  echo -e "  ${GREEN}✓${NC} $1"
  ((PASSED++))
}

fail() {
  echo -e "  ${RED}✗${NC} $1"
  ((FAILED++))
  FAILED_TESTS+=("$1")
}

section() {
  echo ""
  echo -e "${CYAN}[$1]${NC}"
}

info() {
  echo -e "  ${YELLOW}→${NC} $1"
}

# =============================================================================
# Test functions
# =============================================================================

# Generate Makefiles using CMake
# Args: project_dir build_dir
test_cmake_generate() {
  local project_dir="$1"
  local build_dir="$2"
  local test_name="CMake generation (Makefiles)"

  if [ "$CLEAN_BUILDS" = true ] && [ -d "$build_dir" ]; then
    rm -rf "$build_dir"
  fi

  mkdir -p "$build_dir"

  if cmake -G "Unix Makefiles" -S "$project_dir" -B "$build_dir" > "$build_dir/cmake_output.log" 2>&1; then
    pass "$test_name"
    return 0
  else
    fail "$test_name"
    echo "    CMake output:"
    tail -20 "$build_dir/cmake_output.log" | sed 's/^/    /'
    return 1
  fi
}

# Verify Makefile was created
# Args: build_dir
test_makefile_exists() {
  local build_dir="$1"
  local makefile="$build_dir/Makefile"

  if [ -f "$makefile" ]; then
    pass "Makefile exists"
    return 0
  else
    fail "Makefile exists"
    return 1
  fi
}

# Build all targets using make
# Args: build_dir
test_make_build() {
  local build_dir="$1"
  local num_cores=$(sysctl -n hw.ncpu 2>/dev/null || echo 4)

  info "Building with Make -j$num_cores (this may take a while)..."

  if make -C "$build_dir" -j"$num_cores" > "$build_dir/build_output.log" 2>&1; then
    pass "make build"
    return 0
  else
    fail "make build"
    echo "    Build output (last 30 lines):"
    tail -30 "$build_dir/build_output.log" | sed 's/^/    /'
    return 1
  fi
}

# Check bundle exists
# Args: bundle_path bundle_type
test_bundle_exists() {
  local bundle_path="$1"
  local bundle_type="$2"

  if [ -d "$bundle_path" ]; then
    pass "$bundle_type bundle exists"
    return 0
  else
    fail "$bundle_type bundle exists ($bundle_path)"
    return 1
  fi
}

# Check Info.plist exists in bundle
# Args: bundle_path bundle_type
test_info_plist() {
  local bundle_path="$1"
  local bundle_type="$2"
  local plist_path

  # Handle different bundle structures
  if [[ "$bundle_path" == *.framework ]]; then
    plist_path="$bundle_path/Resources/Info.plist"
    # Also check Versions/A/Resources/Info.plist
    if [ ! -f "$plist_path" ]; then
      plist_path="$bundle_path/Versions/A/Resources/Info.plist"
    fi
  else
    plist_path="$bundle_path/Contents/Info.plist"
  fi

  if [ -f "$plist_path" ]; then
    pass "$bundle_type Info.plist exists"
    return 0
  else
    fail "$bundle_type Info.plist exists ($plist_path)"
    return 1
  fi
}

# Check PkgInfo exists in bundle (not applicable to frameworks)
# Args: bundle_path bundle_type
test_pkginfo() {
  local bundle_path="$1"
  local bundle_type="$2"

  # Skip for frameworks
  if [[ "$bundle_path" == *.framework ]]; then
    return 0
  fi

  local pkginfo_path="$bundle_path/Contents/PkgInfo"

  if [ -f "$pkginfo_path" ]; then
    pass "$bundle_type PkgInfo exists"
    return 0
  else
    fail "$bundle_type PkgInfo exists ($pkginfo_path)"
    return 1
  fi
}

# =============================================================================
# Test a complete project
# =============================================================================
# Args: display_name project_dir
test_project() {
  local display_name="$1"
  local project_dir="$2"
  local build_dir="${project_dir}/build-make"

  section "$display_name - Makefiles"

  # Phase 1: Generate Makefiles
  test_cmake_generate "$project_dir" "$build_dir" || return 1

  # Phase 2: Verify project structure
  test_makefile_exists "$build_dir" || return 1

  # Phase 3: Build all targets
  test_make_build "$build_dir" || return 1

  # Phase 4: Verify bundle outputs
  # Make puts output directly in out/ (no config subdirectory)
  local release_dir="$build_dir/out"

  # APP bundle
  local app_path="$release_dir/$display_name.app"
  if test_bundle_exists "$app_path" "APP"; then
    test_info_plist "$app_path" "APP"
    test_pkginfo "$app_path" "APP"
  fi

  # VST3 bundle
  local vst3_path="$release_dir/$display_name.vst3"
  if test_bundle_exists "$vst3_path" "VST3"; then
    test_info_plist "$vst3_path" "VST3"
    test_pkginfo "$vst3_path" "VST3"
  fi

  # CLAP bundle
  local clap_path="$release_dir/$display_name.clap"
  if test_bundle_exists "$clap_path" "CLAP"; then
    test_info_plist "$clap_path" "CLAP"
    test_pkginfo "$clap_path" "CLAP"
  fi

  # AUv2 bundle (component)
  local component_path="$release_dir/$display_name.component"
  if test_bundle_exists "$component_path" "AUv2"; then
    test_info_plist "$component_path" "AUv2"
    test_pkginfo "$component_path" "AUv2"
  fi

  # AUv3 Framework
  local framework_path="$release_dir/${display_name}AU.framework"
  if test_bundle_exists "$framework_path" "AUv3Framework"; then
    test_info_plist "$framework_path" "AUv3Framework"
  fi

  # AUv3 Appex
  local appex_path="$release_dir/${display_name}AUv3.appex"
  if test_bundle_exists "$appex_path" "AUv3Appex"; then
    test_info_plist "$appex_path" "AUv3Appex"
  fi
}

# =============================================================================
# Main test execution
# =============================================================================
echo ""
echo "=== CMake Unix Makefiles Build Test Suite ==="
echo ""
echo "Script directory: $SCRIPT_DIR"
echo "iPlug2 directory: $IPLUG2_DIR"
echo ""

# Test TemplateProject (from iPlug2OOS root)
test_project "TemplateProject" "$SCRIPT_DIR"

# Test IPlugEffect (from iPlug2/Examples)
test_project "IPlugEffect" "$IPLUG2_DIR/Examples/IPlugEffect"

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "=== Summary ==="
TOTAL=$((PASSED + FAILED))
echo "Total: $TOTAL tests"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
  echo ""
  echo "Failed tests:"
  for test in "${FAILED_TESTS[@]}"; do
    echo -e "  ${RED}✗${NC} $test"
  done
fi

# Clean up if requested
if [ "$CLEAN_BUILDS" = true ]; then
  echo ""
  echo "Cleaning up build directories..."
  rm -rf "$SCRIPT_DIR/build-make"
  rm -rf "$IPLUG2_DIR/Examples/IPlugEffect/build-make"
fi

echo ""
if [ $FAILED -gt 0 ]; then
  echo -e "${RED}Some tests failed!${NC}"
  exit 1
else
  echo -e "${GREEN}All tests passed!${NC}"
  exit 0
fi
