#!/bin/bash
# ============================================================
# build_all.sh
# Run this script INSIDE the OMNeT++ MinGW shell (mingwenv.cmd)
# It clones INET 4.4.1 and FLoRa v1.1.0, then builds both.
#
# Usage:
#   1. Open C:\omnetpp\mingwenv.cmd
#   2. Navigate to workspace: cd /c/omnet-workspace/scripts
#   3. Run: bash build_all.sh
# ============================================================

set -e  # Exit on any error

OMNETPP_ROOT="/c/omnetpp"
SAMPLES_DIR="${OMNETPP_ROOT}/samples"
INET_DIR="${SAMPLES_DIR}/inet4.4"
FLORA_DIR="${SAMPLES_DIR}/flora"

INET_VERSION="v4.4.1"
FLORA_VERSION="v1.1.0"

INET_URL="https://github.com/inet-framework/inet/archive/refs/tags/${INET_VERSION}.zip"
FLORA_REPO="https://github.com/florasim/flora.git"

# ─── Colors ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_section() { echo -e "\n${CYAN}══ $1${NC}"; }
print_pass()    { echo -e "${GREEN}  [OK] $1${NC}"; }
print_fail()    { echo -e "${RED}  [FAIL] $1${NC}"; exit 1; }
print_warn()    { echo -e "${YELLOW}  [WARN] $1${NC}"; }
print_info()    { echo "  [INFO] $1"; }

# ─── Preflight checks ────────────────────────────────────────────────────────
print_section "Preflight Checks"

# Check we are in OMNeT++ environment
if ! command -v opp_run &>/dev/null; then
    print_fail "opp_run not found. Are you inside the OMNeT++ MinGW shell?"
fi
print_pass "OMNeT++ environment active: $(opp_run --version 2>&1 | head -1)"

# Check for required tools
for tool in make gcc git wget unzip; do
    if command -v $tool &>/dev/null; then
        print_pass "$tool available"
    else
        print_warn "$tool not found — some steps may fail"
    fi
done

# Check samples directory
if [ ! -d "$SAMPLES_DIR" ]; then
    mkdir -p "$SAMPLES_DIR"
    print_pass "Created samples directory: $SAMPLES_DIR"
else
    print_pass "Samples directory exists: $SAMPLES_DIR"
fi

# ─── INET 4.4.1 ───────────────────────────────────────────────────────────────
print_section "INET Framework ${INET_VERSION}"

if [ -d "$INET_DIR" ]; then
    print_info "INET already at $INET_DIR — skipping download"
else
    print_info "Downloading INET ${INET_VERSION}..."
    cd "$SAMPLES_DIR"

    if command -v wget &>/dev/null; then
        wget -q --show-progress "$INET_URL" -O inet.zip
    elif command -v curl &>/dev/null; then
        curl -L --progress-bar "$INET_URL" -o inet.zip
    else
        print_fail "Neither wget nor curl available. Download manually from $INET_URL"
    fi

    print_info "Extracting INET..."
    unzip -q inet.zip
    # The zip extracts to inet-4.4.1 (without the 'v' prefix)
    mv "inet-4.4.1" "inet4.4" 2>/dev/null || mv "inet-${INET_VERSION#v}" "inet4.4" 2>/dev/null || true
    rm -f inet.zip
    print_pass "INET extracted to $INET_DIR"
fi

# Verify .project exists
if [ ! -f "$INET_DIR/.project" ]; then
    print_fail "INET .project file missing — re-extract the INET zip"
fi
print_pass "INET .project file exists"

# Attempt command-line build
print_info "Building INET (this takes 5-15 minutes)..."
cd "$INET_DIR"

if [ -f "Makefile" ]; then
    make -j$(nproc) MODE=release 2>&1 | tail -5
    if [ -f "out/gcc-release/src/INET.dll" ] || find out/ -name "INET.dll" -o -name "INET.a" 2>/dev/null | grep -q .; then
        print_pass "INET built successfully"
    else
        print_warn "INET build may have issues — check output above"
        print_info "Alternative: Import inet4.4 into OMNeT++ IDE and use Build Project"
    fi
else
    print_warn "No Makefile in INET — use IDE to build (File → Import → inet4.4 → Build)"
fi

# ─── FLoRa v1.1.0 ────────────────────────────────────────────────────────────
print_section "FLoRa Simulator ${FLORA_VERSION}"

if [ -d "$FLORA_DIR" ]; then
    print_info "FLoRa directory exists: $FLORA_DIR"
    # Check if it's a git repo for version confirmation
    if [ -d "$FLORA_DIR/.git" ]; then
        CURRENT_TAG=$(git -C "$FLORA_DIR" describe --tags 2>/dev/null || echo "unknown")
        print_info "Current checkout: $CURRENT_TAG"
        if [ "$CURRENT_TAG" != "$FLORA_VERSION" ] && [ "$CURRENT_TAG" != "${FLORA_VERSION}" ]; then
            print_warn "FLoRa version is '$CURRENT_TAG', expected '$FLORA_VERSION'"
            print_info "To update: cd $FLORA_DIR && git fetch && git checkout $FLORA_VERSION"
        fi
    fi
else
    print_info "Cloning FLoRa ${FLORA_VERSION}..."
    cd "$SAMPLES_DIR"
    git clone "$FLORA_REPO" flora
    cd "$FLORA_DIR"
    git checkout "$FLORA_VERSION"
    print_pass "FLoRa cloned at $FLORA_DIR"
fi

# Verify key files
if [ ! -f "$FLORA_DIR/.project" ]; then
    print_fail "FLoRa .project file missing — re-clone from $FLORA_REPO"
fi
print_pass "FLoRa .project file exists"

if [ ! -f "$FLORA_DIR/simulations/examples/n1000-gw1-ADR.ini" ]; then
    print_warn "ADR scenario file not found — check flora version"
fi

# Build FLoRa
print_info "Building FLoRa..."
cd "$FLORA_DIR"

if [ -f "Makefile" ]; then
    make -j$(nproc) MODE=release 2>&1 | tail -5
    if [ -f "src/flora.exe" ] || find . -name "flora.exe" 2>/dev/null | grep -q .; then
        print_pass "FLoRa built successfully"
    else
        print_warn "FLoRa build may need IDE — ensure Project References point to inet4.4"
        print_info "IDE steps: right-click flora → Properties → Project References → check inet4.4"
    fi
else
    print_warn "No Makefile in FLoRa — use IDE to build"
fi

# ─── Final Report ─────────────────────────────────────────────────────────────
print_section "Build Summary"

ERRORS=0
for CHECK in \
    "$OMNETPP_ROOT/bin/opp_run.exe:opp_run.exe" \
    "$INET_DIR/.project:INET .project" \
    "$FLORA_DIR/.project:FLoRa .project" \
    "$FLORA_DIR/simulations/omnetpp.ini:Default simulation" \
    "$FLORA_DIR/simulations/examples/n1000-gw1-ADR.ini:ADR scenario"; do
    PATH_="${CHECK%%:*}"
    LABEL="${CHECK##*:}"
    if [ -e "$PATH_" ]; then
        print_pass "$LABEL"
    else
        echo -e "${RED}  [MISSING] $LABEL${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}══════════════════════════════════════${NC}"
    echo -e "${GREEN}  FLoRa READY!${NC}"
    echo -e "${GREEN}══════════════════════════════════════${NC}"
    echo ""
    echo "  To run first simulation (GUI):"
    echo "    Open OMNeT++ IDE → flora → simulations/omnetpp.ini → Run As"
    echo ""
    echo "  To run ADR baseline (command line):"
    echo "    cd $FLORA_DIR/simulations"
    echo "    ../src/flora -u Cmdenv examples/n1000-gw1-ADR.ini"
    echo ""
    echo "  To export results:"
    echo "    cd $FLORA_DIR/simulations/results"
    echo "    opp_scavetool export General-0.sca -o results.csv"
else
    echo -e "${YELLOW}  $ERRORS item(s) need attention. See TROUBLESHOOTING.md${NC}"
fi
