#!/bin/bash
# test-cmake-xcode.sh - Test CMake Xcode project generation for iPlug2
#
# Tests that the CMake build system correctly generates Xcode projects
# and all plugin formats build successfully.
#
# Usage: ./test-cmake-xcode.sh [--clean]
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

# Generate Xcode project using CMake
# Args: project_dir build_dir [universal]
test_cmake_generate() {
  local project_dir="$1"
  local build_dir="$2"
  local universal="${3:-false}"
  local test_name="CMake generation"

  if [ "$CLEAN_BUILDS" = true ] && [ -d "$build_dir" ]; then
    rm -rf "$build_dir"
  fi

  mkdir -p "$build_dir"

  local cmake_args="-G Xcode -S $project_dir -B $build_dir"
  if [ "$universal" = "true" ]; then
    cmake_args="$cmake_args -DIPLUG2_UNIVERSAL=ON"
    test_name="CMake generation (universal)"
  fi

  if cmake $cmake_args > "$build_dir/cmake_output.log" 2>&1; then
    pass "$test_name"
    return 0
  else
    fail "$test_name"
    echo "    CMake output:"
    tail -20 "$build_dir/cmake_output.log" | sed 's/^/    /'
    return 1
  fi
}

# Verify Xcode project was created
# Args: build_dir project_name
test_xcodeproj_exists() {
  local build_dir="$1"
  local project_name="$2"
  local xcodeproj="$build_dir/$project_name.xcodeproj"

  if [ -d "$xcodeproj" ]; then
    pass "$project_name.xcodeproj exists"
    return 0
  else
    fail "$project_name.xcodeproj exists"
    return 1
  fi
}

# Build all targets using xcodebuild
# Args: build_dir project_name universal
test_xcode_build() {
  local build_dir="$1"
  local project_name="$2"
  local universal="${3:-false}"
  local xcodeproj="$build_dir/$project_name.xcodeproj"

  info "Building $project_name (this may take a while)..."

  # For universal builds, use generic destination to build for all architectures
  local destination_args=""
  if [ "$universal" = "true" ]; then
    destination_args="-destination generic/platform=macOS"
  fi

  if xcodebuild -project "$xcodeproj" \
                -scheme ALL_BUILD \
                -configuration Release \
                $destination_args \
                -quiet \
                > "$build_dir/build_output.log" 2>&1; then
    pass "xcodebuild ALL_BUILD"
    return 0
  else
    fail "xcodebuild ALL_BUILD"
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

# Check binary contains both architectures for universal builds
# Args: executable_path bundle_type
test_universal_binary() {
  local executable_path="$1"
  local bundle_type="$2"

  if [ ! -f "$executable_path" ]; then
    fail "$bundle_type universal (executable not found)"
    return 1
  fi

  local archs
  archs=$(lipo -archs "$executable_path" 2>/dev/null)

  if [[ "$archs" == *"arm64"* ]] && [[ "$archs" == *"x86_64"* ]]; then
    pass "$bundle_type universal (arm64 + x86_64)"
    return 0
  else
    fail "$bundle_type universal (got: $archs)"
    return 1
  fi
}

# Get path to main executable in a bundle
# Args: bundle_path project_name
get_bundle_executable() {
  local bundle_path="$1"
  local project_name="$2"

  if [[ "$bundle_path" == *.app ]]; then
    echo "$bundle_path/Contents/MacOS/$project_name"
  elif [[ "$bundle_path" == *.vst3 ]]; then
    echo "$bundle_path/Contents/MacOS/$project_name"
  elif [[ "$bundle_path" == *.clap ]]; then
    echo "$bundle_path/Contents/MacOS/$project_name"
  elif [[ "$bundle_path" == *.component ]]; then
    echo "$bundle_path/Contents/MacOS/$project_name"
  elif [[ "$bundle_path" == *.framework ]]; then
    echo "$bundle_path/Versions/A/${project_name}AU"
  elif [[ "$bundle_path" == *.appex ]]; then
    echo "$bundle_path/Contents/MacOS/${project_name}"
  fi
}

# =============================================================================
# Test a complete project
# =============================================================================
# Args: display_name project_dir build_type xcodeproj_name
test_project() {
  local display_name="$1"
  local project_dir="$2"
  local build_type="$3"  # "native" or "universal"
  local xcodeproj_name="$4"  # Name of the .xcodeproj (may differ from display_name)
  local build_dir="${project_dir}/build-xcode-${build_type}"
  local universal="false"

  if [ "$build_type" = "universal" ]; then
    universal="true"
  fi

  # Capitalize build_type (bash 3.2 compatible)
  local build_type_cap
  case "$build_type" in
    native) build_type_cap="Native" ;;
    universal) build_type_cap="Universal" ;;
    *) build_type_cap="$build_type" ;;
  esac

  section "$display_name - $build_type_cap"

  # Phase 1: Generate Xcode project
  test_cmake_generate "$project_dir" "$build_dir" "$universal" || return 1

  # Phase 2: Verify project structure
  test_xcodeproj_exists "$build_dir" "$xcodeproj_name" || return 1

  # Phase 3: Build all targets
  test_xcode_build "$build_dir" "$xcodeproj_name" "$universal" || return 1

  # Phase 4: Verify bundle outputs
  # CMake Xcode generator puts output in out/Release/ by default
  local release_dir="$build_dir/out/Release"

  # APP bundle
  local app_path="$release_dir/$display_name.app"
  if test_bundle_exists "$app_path" "APP"; then
    test_info_plist "$app_path" "APP"
    test_pkginfo "$app_path" "APP"
    if [ "$universal" = "true" ]; then
      test_universal_binary "$(get_bundle_executable "$app_path" "$display_name")" "APP"
    fi
  fi

  # VST3 bundle
  local vst3_path="$release_dir/$display_name.vst3"
  if test_bundle_exists "$vst3_path" "VST3"; then
    test_info_plist "$vst3_path" "VST3"
    test_pkginfo "$vst3_path" "VST3"
    if [ "$universal" = "true" ]; then
      test_universal_binary "$(get_bundle_executable "$vst3_path" "$display_name")" "VST3"
    fi
  fi

  # CLAP bundle
  local clap_path="$release_dir/$display_name.clap"
  if test_bundle_exists "$clap_path" "CLAP"; then
    test_info_plist "$clap_path" "CLAP"
    test_pkginfo "$clap_path" "CLAP"
    if [ "$universal" = "true" ]; then
      test_universal_binary "$(get_bundle_executable "$clap_path" "$display_name")" "CLAP"
    fi
  fi

  # AUv2 bundle (component)
  local component_path="$release_dir/$display_name.component"
  if test_bundle_exists "$component_path" "AUv2"; then
    test_info_plist "$component_path" "AUv2"
    test_pkginfo "$component_path" "AUv2"
    if [ "$universal" = "true" ]; then
      test_universal_binary "$(get_bundle_executable "$component_path" "$display_name")" "AUv2"
    fi
  fi

  # AUv3 Framework
  local framework_path="$release_dir/${display_name}AU.framework"
  if test_bundle_exists "$framework_path" "AUv3Framework"; then
    test_info_plist "$framework_path" "AUv3Framework"
    if [ "$universal" = "true" ]; then
      test_universal_binary "$(get_bundle_executable "$framework_path" "$display_name")" "AUv3Framework"
    fi
  fi

  # AUv3 Appex (standalone in release dir - embedding tested separately)
  local appex_path="$release_dir/${display_name}AUv3.appex"
  if test_bundle_exists "$appex_path" "AUv3Appex"; then
    test_info_plist "$appex_path" "AUv3Appex"
    if [ "$universal" = "true" ]; then
      test_universal_binary "$(get_bundle_executable "$appex_path" "$display_name")" "AUv3Appex"
    fi
  fi
}

# =============================================================================
# Main test execution
# =============================================================================
echo ""
echo "=== CMake Xcode Generator Test Suite ==="
echo ""
echo "Script directory: $SCRIPT_DIR"
echo "iPlug2 directory: $IPLUG2_DIR"
echo ""

# Test TemplateProject (from iPlug2OOS root)
# xcodeproj is named after the root CMake project (iPlug2OOS)
test_project "TemplateProject" "$SCRIPT_DIR" "native" "iPlug2OOS"
test_project "TemplateProject" "$SCRIPT_DIR" "universal" "iPlug2OOS"

# Test IPlugEffect (from iPlug2/Examples)
# xcodeproj matches the plugin name
test_project "IPlugEffect" "$IPLUG2_DIR/Examples/IPlugEffect" "native" "IPlugEffect"
test_project "IPlugEffect" "$IPLUG2_DIR/Examples/IPlugEffect" "universal" "IPlugEffect"

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
  rm -rf "$SCRIPT_DIR/build-xcode-native"
  rm -rf "$SCRIPT_DIR/build-xcode-universal"
  rm -rf "$IPLUG2_DIR/Examples/IPlugEffect/build-xcode-native"
  rm -rf "$IPLUG2_DIR/Examples/IPlugEffect/build-xcode-universal"
fi

echo ""
if [ $FAILED -gt 0 ]; then
  echo -e "${RED}Some tests failed!${NC}"
  exit 1
else
  echo -e "${GREEN}All tests passed!${NC}"
  exit 0
fi
