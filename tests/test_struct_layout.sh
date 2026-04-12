#!/usr/bin/env bash
# Phase 1 CI gate: Python ctypes struct layout must match C struct layout
# for every (dram_type x two_channel) combination supported by the tool.
#
# Exit 0 on success, 1 on any diff.
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail=0
for dt in 2 3; do
  for ch in 0 1; do
    case "$dt" in
      2) dt_name=lpddr4 ;;
      3) dt_name=lpddr5 ;;
    esac
    tag="${dt_name}_ch${ch}"

    gcc -std=c99 -Wall -O0 \
        -DDDR_TYPE=$dt -DDDR_TWO_CHANNEL=$ch \
        -I. \
        tools/dump_struct_layout.c \
        -o "$TMP/dump_c_$tag" 2> "$TMP/cc_err_$tag" || {
      echo "FAIL: gcc build failed for $tag"; cat "$TMP/cc_err_$tag"; fail=1; continue; }

    "$TMP/dump_c_$tag" > "$TMP/c_$tag.txt"
    python3 tools/dump_struct_layout.py \
        --dram-type=$dt --two-channel=$ch > "$TMP/py_$tag.txt"

    if ! diff -u "$TMP/c_$tag.txt" "$TMP/py_$tag.txt" > "$TMP/diff_$tag.txt"; then
      echo "FAIL: struct layout diverges for $tag:"
      cat "$TMP/diff_$tag.txt"
      fail=1
    else
      echo "OK: $tag"
    fi
  done
done

exit $fail
