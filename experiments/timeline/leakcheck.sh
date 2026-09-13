#!/bin/sh
# Pre-send check (docs/security.md). Run on any page before it leaves the laptop.
fail=0
for f in "$@"; do
  printf '%s\n' "$f"
  for pat in '/Users/[a-zA-Z0-9_]*' 'file://' '"gps"' '\b[0-9]\{1,2\}\.[0-9]\{5,\}'; do
    n=$(grep -oE "$pat" "$f" 2>/dev/null | wc -l | tr -d ' ')
    [ "$n" -gt 0 ] && { printf '  LEAK  %-28s %s\n' "$pat" "$n"; fail=1; }
  done
  [ "$fail" -eq 0 ] && printf '  clean\n'
done
exit $fail
