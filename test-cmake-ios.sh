#!/bin/bash
# test-cmake-ios.sh - Test CMake iOS builds for iPlug2 examples
#
# Tests that all iPlug2 examples with CMakeLists.txt files build
# successfully for iOS (simulator).
#
# Usage: ./test-cmake-ios.sh [--clean] [--device]
#   --clean: Remove build directories before tests
#   --device: Build for physical device instead of simulator

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IPLUG2_DIR="$SCRIPT_DIR/iPlug2"
EXAMPLES_DIR="$IPLUG2_DIR/Examples"

# Test counters
PASSED=0
FAILED=0
FAILED_TESTS=()

# Options
CLEAN_BUILDS=false
BUILD_FOR_DEVICE=false

for arg in "$@"; do
  case $arg in
    --clean)
      CLEAN_BUILDS=true
      ;;
    --device)
      BUILD_FOR_DEVICE=true
      ;;
  esac
done

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

# Generate Xcode project for iOS using CMake
# Args: project_dir build_dir
test_cmake_generate_ios() {
  local project_dir="$1"
  local build_dir="$2"
  local test_name="CMake iOS generation"

  if [ "$CLEAN_BUILDS" = true ] && [ -d "$build_dir" ]; then
    rm -rf "$build_dir"
  fi

  mkdir -p "$build_dir"

  local cmake_args="-G Xcode -S $project_dir -B $build_dir -DCMAKE_SYSTEM_NAME=iOS"

  if [ "$BUILD_FOR_DEVICE" = false ]; then
    cmake_args="$cmake_args -DCMAKE_OSX_SYSROOT=iphonesimulator"
    test_name="CMake iOS Simulator generation"
  else
    cmake_args="$cmake_args -DCMAKE_OSX_SYSROOT=iphoneos"
    test_name="CMake iOS Device generation"
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

# Build iOS targets using xcodebuild
# Args: build_dir project_name
test_xcode_build_ios() {
  local build_dir="$1"
  local project_name="$2"
  local xcodeproj="$build_dir/$project_name.xcodeproj"

  info "Building $project_name for iOS (this may take a while)..."

  local sdk="iphonesimulator"
  local destination="generic/platform=iOS Simulator"
  if [ "$BUILD_FOR_DEVICE" = true ]; then
    sdk="iphoneos"
    destination="generic/platform=iOS"
  fi

  # Build ALL_BUILD scheme which builds all targets
  if xcodebuild -project "$xcodeproj" \
                -scheme ALL_BUILD \
                -configuration Release \
                -sdk "$sdk" \
                -destination "$destination" \
                -quiet \
                CODE_SIGNING_ALLOWED=NO \
                > "$build_dir/build_output.log" 2>&1; then
    pass "xcodebuild iOS ALL_BUILD"
    return 0
  else
    fail "xcodebuild iOS ALL_BUILD"
    echo "    Build output (last 40 lines):"
    tail -40 "$build_dir/build_output.log" | sed 's/^/    /'
    return 1
  fi
}

# Check iOS bundle exists (flat structure)
# Args: bundle_path bundle_type
test_ios_bundle_exists() {
  local bundle_path="$1"
  local bundle_type="$2"

  if [ -d "$bundle_path" ]; then
    pass "$bundle_type iOS bundle exists"
    return 0
  else
    fail "$bundle_type iOS bundle exists ($bundle_path)"
    return 1
  fi
}

# Check Info.plist exists in iOS bundle (flat structure)
# Args: bundle_path bundle_type
test_ios_info_plist() {
  local bundle_path="$1"
  local bundle_type="$2"
  local plist_path="$bundle_path/Info.plist"

  if [ -f "$plist_path" ]; then
    pass "$bundle_type iOS Info.plist exists"
    return 0
  else
    fail "$bundle_type iOS Info.plist exists ($plist_path)"
    return 1
  fi
}

# =============================================================================
# Test a complete iOS project
# =============================================================================
# Args: display_name project_dir xcodeproj_name
test_ios_project() {
  local display_name="$1"
  local project_dir="$2"
  local xcodeproj_name="$3"
  local build_dir="${project_dir}/build-ios-xcode"

  local platform_name="Simulator"
  if [ "$BUILD_FOR_DEVICE" = true ]; then
    platform_name="Device"
  fi

  section "$display_name - iOS $platform_name"

  # Phase 1: Generate Xcode project for iOS
  test_cmake_generate_ios "$project_dir" "$build_dir" || return 1

  # Phase 2: Verify project structure
  test_xcodeproj_exists "$build_dir" "$xcodeproj_name" || return 1

  # Phase 3: Build all iOS targets
  test_xcode_build_ios "$build_dir" "$xcodeproj_name" || return 1

  # Phase 4: Verify iOS bundle outputs
  # CMake Xcode generator puts output in out/Release/ (not out/Release-iphonesimulator/)
  local release_dir="$build_dir/out/Release"

  # iOS App bundle
  local app_path="$release_dir/$display_name.app"
  if test_ios_bundle_exists "$app_path" "iOS App"; then
    test_ios_info_plist "$app_path" "iOS App"
  fi

  # iOS AUv3 Framework
  local framework_path="$release_dir/${display_name}AU.framework"
  if test_ios_bundle_exists "$framework_path" "iOS AUv3Framework"; then
    test_ios_info_plist "$framework_path" "iOS AUv3Framework"
  fi

  # iOS AUv3 Appex
  local appex_path="$release_dir/${display_name}AUv3.appex"
  if test_ios_bundle_exists "$appex_path" "iOS AUv3Appex"; then
    test_ios_info_plist "$appex_path" "iOS AUv3Appex"
  fi

  return 0
}

# =============================================================================
# Main test execution
# =============================================================================
echo ""
echo "=== CMake iOS Build Test Suite ==="
echo ""
echo "Script directory: $SCRIPT_DIR"
echo "iPlug2 directory: $IPLUG2_DIR"
if [ "$BUILD_FOR_DEVICE" = true ]; then
  echo "Target: iOS Device (iphoneos)"
else
  echo "Target: iOS Simulator (iphonesimulator)"
fi
echo ""

# List of examples with CMakeLists.txt that have iOS support
# Exclusions:
#   - IPlugWebUI: WebView has macOS-specific code (NSEventModifierFlag*) that doesn't compile for iOS
#   - IPlugSwiftUI: Uses SwiftUI APIs (TimelineView, etc.) that require iOS 15+, but iPlug2 targets iOS 14
EXAMPLES=(
  "IPlugEffect"
  "IPlugInstrument"
  "IPlugControls"
  "IPlugConvoEngine"
)

# Test each example
for example in "${EXAMPLES[@]}"; do
  example_dir="$EXAMPLES_DIR/$example"

  if [ -f "$example_dir/CMakeLists.txt" ]; then
    test_ios_project "$example" "$example_dir" "$example"
  else
    section "$example"
    info "Skipping - no CMakeLists.txt found"
  fi
done

# Also test TemplateProject from iPlug2OOS root
test_ios_project "TemplateProject" "$SCRIPT_DIR" "iPlug2OOS"

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
  rm -rf "$SCRIPT_DIR/build-ios-xcode"
  for example in "${EXAMPLES[@]}"; do
    rm -rf "$EXAMPLES_DIR/$example/build-ios-xcode"
  done
fi

echo ""
if [ $FAILED -gt 0 ]; then
  echo -e "${RED}Some tests failed!${NC}"
  exit 1
else
  echo -e "${GREEN}All tests passed!${NC}"
  exit 0
fi
