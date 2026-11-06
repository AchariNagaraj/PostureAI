#!/usr/bin/env bash
# render-build.sh - Build script for Render Native Python environment
set -e

echo "=== PostureAI: Render Build Started ==="

# 1. Install Python dependencies
echo "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# 2. Obtain Linux system graphics libraries for MediaPipe
LIBS_DIR="$(pwd)/.libs"
mkdir -p "$LIBS_DIR"

INSTALLED=0
if command -v apt-get &> /dev/null; then
    echo "Attempting apt-get install for graphics libraries..."
    if apt-get update -qq && apt-get install -y --no-install-recommends libgles2 libegl1 libgl1 libglvnd0 libglapi-mesa libglib2.0-0 2>/dev/null; then
        echo "Successfully installed graphics libraries via apt-get."
        INSTALLED=1
    elif command -v sudo &> /dev/null && sudo apt-get update -qq && sudo apt-get install -y --no-install-recommends libgles2 libegl1 libgl1 libglvnd0 libglapi-mesa libglib2.0-0 2>/dev/null; then
        echo "Successfully installed graphics libraries via sudo apt-get."
        INSTALLED=1
    fi
fi

# Fallback: If apt-get install failed (unprivileged user), extract deb packages to .libs
if [ "$INSTALLED" -eq 0 ] && command -v apt-get &> /dev/null && command -v dpkg &> /dev/null; then
    echo "Root unavailable; downloading and extracting packages to .libs..."
    TMP_DIR="$(mktemp -d)"
    cd "$TMP_DIR"
    apt-get download libgles2 libglvnd0 libglapi-mesa libegl1 libgl1 libglib2.0-0 2>/dev/null || true
    for deb in *.deb; do
        [ -f "$deb" ] && dpkg -x "$deb" "$TMP_DIR/ext" 2>/dev/null || true
    done
    if [ -d "$TMP_DIR/ext" ]; then
        find "$TMP_DIR/ext" -type f -name "*.so*" -exec cp -L {} "$LIBS_DIR/" \; 2>/dev/null || true
        find "$TMP_DIR/ext" -type l -name "*.so*" -exec cp -d {} "$LIBS_DIR/" \; 2>/dev/null || true
    fi
    rm -rf "$TMP_DIR"
    cd - > /dev/null
fi

# Ensure standard soname symlinks exist in .libs
if [ -d "$LIBS_DIR" ]; then
    cd "$LIBS_DIR"
    [ -f libGLESv2.so.2.* ] && [ ! -f libGLESv2.so.2 ] && ln -sf libGLESv2.so.2.* libGLESv2.so.2 || true
    [ -f libEGL.so.1.* ] && [ ! -f libEGL.so.1 ] && ln -sf libEGL.so.1.* libEGL.so.1 || true
    [ -f libGL.so.1.* ] && [ ! -f libGL.so.1 ] && ln -sf libGL.so.1.* libGL.so.1 || true
    cd - > /dev/null
    echo "Contents of $LIBS_DIR:"
    ls -la "$LIBS_DIR" || true
fi

echo "=== PostureAI: Render Build Complete ==="
