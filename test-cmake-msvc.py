#!/usr/bin/env python3
"""Test CMake Visual Studio (MSVC) build for iPlug2.

Tests that the CMake build system correctly generates Visual Studio projects
and all plugin formats build successfully.

Usage: python test-cmake-msvc.py [options]

Options:
  --clean             Remove build directories before and after tests
  --all               Test all graphics backend configurations
  --backends BACKEND  Test specific backend group: 'nanovg' or 'skia'

Without --all or --backends, only the default backend (NanoVG-GL2) is tested.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

# Enable UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    os.system("")  # Enable ANSI escape codes

SCRIPT_DIR = Path(__file__).parent.resolve()
IPLUG2_DIR = SCRIPT_DIR / "iPlug2"

BUILD_CONFIG = "Release"
VS_GENERATOR = "Visual Studio 17 2022"

# Test counters
passed = 0
failed = 0
failed_tests = []


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"


def pass_test(name: str):
    global passed
    print(f"  {Colors.GREEN}✓{Colors.RESET} {name}")
    passed += 1


def fail_test(name: str):
    global failed
    print(f"  {Colors.RED}✗{Colors.RESET} {name}")
    failed += 1
    failed_tests.append(name)


def section(name: str):
    print(f"\n{Colors.CYAN}[{name}]{Colors.RESET}")


def info(msg: str):
    print(f"  {Colors.YELLOW}→{Colors.RESET} {msg}")


def run_command(cmd: list[str], cwd: Path = None, log_file: Path = None) -> tuple[int, str]:
    """Run a command and return (returncode, output)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr
        if log_file:
            log_file.write_text(output, encoding="utf-8")
        return result.returncode, output
    except Exception as e:
        return 1, str(e)


def test_cmake_generate(
    project_dir: Path,
    build_dir: Path,
    clean: bool,
    backend: str = None,
    renderer: str = None,
) -> bool:
    """Generate Visual Studio solution using CMake."""
    if clean and build_dir.exists():
        import shutil
        shutil.rmtree(build_dir)

    build_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "cmake",
        "-G", VS_GENERATOR,
        "-A", "x64",
        "-S", str(project_dir),
        "-B", str(build_dir),
    ]
    if backend:
        cmd.append(f"-DIGRAPHICS_BACKEND={backend}")
    if renderer:
        cmd.append(f"-DIGRAPHICS_RENDERER={renderer}")

    returncode, output = run_command(cmd, log_file=build_dir / "cmake_output.log")

    if returncode == 0:
        pass_test("CMake generation")
        return True
    else:
        fail_test("CMake generation")
        print("    CMake output (last 20 lines):")
        for line in output.splitlines()[-20:]:
            print(f"    {line}")
        return False


def test_solution_exists(build_dir: Path) -> bool:
    """Check that a .sln file was created."""
    sln_files = list(build_dir.glob("*.sln"))
    if sln_files:
        pass_test(f"Solution file exists ({sln_files[0].name})")
        return True
    else:
        fail_test("Solution file exists")
        return False


def test_build_target(build_dir: Path, target: str) -> bool:
    """Build a specific target."""
    cmd = [
        "cmake",
        "--build", str(build_dir),
        "--config", BUILD_CONFIG,
        "--target", target,
    ]

    returncode, output = run_command(cmd, log_file=build_dir / f"build_{target}.log")

    if returncode == 0:
        pass_test(f"Build {target}")
        return True
    else:
        fail_test(f"Build {target}")
        print("    Build output (last 15 lines):")
        for line in output.splitlines()[-15:]:
            print(f"    {line}")
        return False


def test_build_all(build_dir: Path) -> bool:
    """Build all targets."""
    info("Building with MSBuild (this may take a while)...")

    cmd = [
        "cmake",
        "--build", str(build_dir),
        "--config", BUILD_CONFIG,
    ]

    returncode, output = run_command(cmd, log_file=build_dir / "build_output.log")

    if returncode == 0:
        pass_test(f"MSBuild {BUILD_CONFIG}")
        return True
    else:
        fail_test(f"MSBuild {BUILD_CONFIG}")
        print("    Build output (last 20 lines):")
        for line in output.splitlines()[-20:]:
            print(f"    {line}")
        return False


def test_output_exists(path: Path, name: str) -> bool:
    """Check that an output file/directory exists."""
    if path.exists():
        pass_test(f"{name} exists")
        return True
    else:
        fail_test(f"{name} missing: {path}")
        return False


def test_vst3_bundle(release_dir: Path, plugin_name: str) -> None:
    """Test VST3 bundle structure."""
    vst3_path = release_dir / f"{plugin_name}.vst3"
    if test_output_exists(vst3_path, "VST3 bundle"):
        test_output_exists(vst3_path / "Contents" / "x86_64-win", "VST3 x86_64-win directory")


def test_project(
    display_name: str,
    project_dir: Path,
    clean: bool,
    build_targets: list[str] = None,
    backend_config: dict = None,
):
    """Test a complete project build."""
    # Build directory includes backend config name for isolation
    config_suffix = f"-{backend_config['name']}" if backend_config else ""
    build_dir = project_dir / f"build-msvc{config_suffix}"

    section(f"{display_name} - MSVC{config_suffix}")

    # Phase 1: Generate
    backend = backend_config["backend"] if backend_config else None
    renderer = backend_config["renderer"] if backend_config else None
    if not test_cmake_generate(project_dir, build_dir, clean, backend, renderer):
        return

    # Phase 2: Verify solution
    if not test_solution_exists(build_dir):
        return

    # Phase 3: Build
    if build_targets:
        info("Building specific targets...")
        for target in build_targets:
            test_build_target(build_dir, target)
    else:
        if not test_build_all(build_dir):
            return

    # Phase 4: Verify outputs
    release_dir = build_dir / "out"

    test_output_exists(release_dir / f"{display_name}.exe", "APP executable")
    test_vst3_bundle(release_dir, display_name)
    test_output_exists(release_dir / f"{display_name}.clap", "CLAP plugin")


EXAMPLES_DIR = IPLUG2_DIR / "Examples"

# Project configurations
# - name: Display name
# - path: Path to project directory (relative to appropriate base)
# - uses_igraphics: Whether the project uses IGraphics (needs backend matrix testing)
# - build_targets: Specific targets to build (None = build all)
# - is_example: Whether it's an iPlug2 example (uses EXAMPLES_DIR) or OOS project (uses SCRIPT_DIR)

OOS_PROJECTS = [
    {
        "name": "TemplateProject",
        "path": "TemplateProject",
        "uses_igraphics": True,
        "build_targets": ["TemplateProject-app", "TemplateProject-vst3", "TemplateProject-clap"],
    },
    {
        "name": "VisageTemplate",
        "path": "VisageTemplate",
        "uses_igraphics": False,  # Uses Visage, not IGraphics
        "build_targets": ["VisageTemplate-app", "VisageTemplate-vst3", "VisageTemplate-clap"],
    },
]

# iPlug2 Examples to test (must have CMakeLists.txt)
# Exclusions:
#   - IPlugSwiftUI: SwiftUI is macOS/iOS only
#   - IPlugWebUI: WebView2 support may require additional setup
EXAMPLE_PROJECTS = [
    {"name": "IPlugEffect", "uses_igraphics": True},
    {"name": "IPlugInstrument", "uses_igraphics": True},
    {"name": "IPlugControls", "uses_igraphics": True},
    {"name": "IPlugConvoEngine", "uses_igraphics": True},
]

# Graphics backend configurations for Windows
# METAL is macOS/iOS only, so not included here
BACKEND_CONFIGS = [
    {"name": "NanoVG-GL2", "backend": "NANOVG", "renderer": "GL2"},
    {"name": "NanoVG-GL3", "backend": "NANOVG", "renderer": "GL3"},
    {"name": "Skia-GL3", "backend": "SKIA", "renderer": "GL3"},
    {"name": "Skia-CPU", "backend": "SKIA", "renderer": "CPU"},
]

DEFAULT_BACKEND = BACKEND_CONFIGS[0]  # NanoVG-GL2


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Test CMake MSVC builds for iPlug2 with various graphics backends."
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove build directories before and after tests",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Test all graphics backend configurations",
    )
    parser.add_argument(
        "--backends",
        choices=["nanovg", "skia"],
        help="Test specific backend group: 'nanovg' or 'skia'",
    )
    return parser.parse_args()


def get_backend_configs(args) -> list[dict]:
    """Get the list of backend configurations to test based on args."""
    if args.all:
        return BACKEND_CONFIGS
    elif args.backends == "nanovg":
        return [c for c in BACKEND_CONFIGS if c["backend"] == "NANOVG"]
    elif args.backends == "skia":
        return [c for c in BACKEND_CONFIGS if c["backend"] == "SKIA"]
    else:
        return [DEFAULT_BACKEND]


def cleanup(clean: bool, configs: list[dict]):
    """Clean up build directories if requested."""
    if not clean:
        return

    import shutil

    print("\nCleaning up build directories...")

    dirs_to_clean = []

    # OOS projects
    for proj in OOS_PROJECTS:
        proj_dir = SCRIPT_DIR / proj["path"]
        if proj["uses_igraphics"]:
            for config in configs:
                dirs_to_clean.append(proj_dir / f"build-msvc-{config['name']}")
        else:
            dirs_to_clean.append(proj_dir / "build-msvc")

    # Example projects
    for proj in EXAMPLE_PROJECTS:
        proj_dir = EXAMPLES_DIR / proj["name"]
        if proj["uses_igraphics"]:
            for config in configs:
                dirs_to_clean.append(proj_dir / f"build-msvc-{config['name']}")
        else:
            dirs_to_clean.append(proj_dir / "build-msvc")

    for d in dirs_to_clean:
        if d.exists():
            try:
                shutil.rmtree(d)
                print(f"  Removed {d}")
            except PermissionError as e:
                print(f"  Warning: Could not remove {d}: {e}")


def test_project_with_configs(proj: dict, proj_dir: Path, args, configs: list[dict]):
    """Test a project, applying backend matrix only if it uses IGraphics."""
    if proj["uses_igraphics"]:
        # Test with each backend configuration
        for config in configs:
            test_project(
                proj["name"],
                proj_dir,
                args.clean,
                build_targets=proj.get("build_targets"),
                backend_config=config,
            )
    else:
        # Non-IGraphics project: test once without backend config
        print(f"\n{'='*60}")
        print(f"  {proj['name']} (no IGraphics - single build)")
        print(f"{'='*60}")
        test_project(
            proj["name"],
            proj_dir,
            args.clean,
            build_targets=proj.get("build_targets"),
            backend_config=None,
        )


def main():
    args = parse_args()
    configs = get_backend_configs(args)

    print("\n=== CMake MSVC Build Test Suite ===\n")
    print(f"Script directory: {SCRIPT_DIR}")
    print(f"iPlug2 directory: {IPLUG2_DIR}")
    print(f"VS Generator: {VS_GENERATOR}")
    print(f"Build config: {BUILD_CONFIG}")
    print(f"Backend configs: {', '.join(c['name'] for c in configs)}")

    # Test IGraphics projects with backend matrix
    igraphics_projects = [p for p in OOS_PROJECTS + EXAMPLE_PROJECTS if p["uses_igraphics"]]
    if igraphics_projects:
        for config in configs:
            print(f"\n{'='*60}")
            print(f"  Backend: {config['name']} ({config['backend']}/{config['renderer']})")
            print(f"{'='*60}")

            # OOS projects with IGraphics
            for proj in OOS_PROJECTS:
                if proj["uses_igraphics"]:
                    proj_dir = SCRIPT_DIR / proj["path"]
                    if (proj_dir / "CMakeLists.txt").exists():
                        test_project(
                            proj["name"],
                            proj_dir,
                            args.clean,
                            build_targets=proj.get("build_targets"),
                            backend_config=config,
                        )

            # Example projects with IGraphics
            for proj in EXAMPLE_PROJECTS:
                if proj["uses_igraphics"]:
                    proj_dir = EXAMPLES_DIR / proj["name"]
                    if (proj_dir / "CMakeLists.txt").exists():
                        test_project(
                            proj["name"],
                            proj_dir,
                            args.clean,
                            build_targets=proj.get("build_targets"),
                            backend_config=config,
                        )

    # Test non-IGraphics projects (only once, no backend matrix)
    non_igraphics_projects = [p for p in OOS_PROJECTS + EXAMPLE_PROJECTS if not p["uses_igraphics"]]
    if non_igraphics_projects:
        print(f"\n{'='*60}")
        print(f"  Non-IGraphics Projects (single build)")
        print(f"{'='*60}")

        for proj in OOS_PROJECTS:
            if not proj["uses_igraphics"]:
                proj_dir = SCRIPT_DIR / proj["path"]
                if (proj_dir / "CMakeLists.txt").exists():
                    test_project(
                        proj["name"],
                        proj_dir,
                        args.clean,
                        build_targets=proj.get("build_targets"),
                        backend_config=None,
                    )

        for proj in EXAMPLE_PROJECTS:
            if not proj["uses_igraphics"]:
                proj_dir = EXAMPLES_DIR / proj["name"]
                if (proj_dir / "CMakeLists.txt").exists():
                    test_project(
                        proj["name"],
                        proj_dir,
                        args.clean,
                        build_targets=proj.get("build_targets"),
                        backend_config=None,
                    )

    # Summary
    print("\n=== Summary ===")
    total = passed + failed
    print(f"Total: {total} tests")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")

    if failed_tests:
        print("\nFailed tests:")
        for test in failed_tests:
            print(f"  {Colors.RED}✗{Colors.RESET} {test}")

    cleanup(args.clean, configs)

    print()
    if failed > 0:
        print(f"{Colors.RED}Some tests failed!{Colors.RESET}")
        sys.exit(1)
    else:
        print(f"{Colors.GREEN}All tests passed!{Colors.RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
