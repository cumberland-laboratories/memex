#!/bin/bash
# memex-lint.sh — Mechanical invariant checker for the Memex
# Read-only. Reports findings, changes nothing.
# Usage: bash scripts/memex-lint.sh

MEMEX_DIR="$(cd "$(dirname "$0")/.." && pwd)/memex"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ERRORS=0
WARNINGS=0

RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m'

error() { echo -e "${RED}ERROR:${NC} $1"; ((ERRORS++)); }
warn()  { echo -e "${YELLOW}WARN:${NC}  $1"; ((WARNINGS++)); }
ok()    { echo -e "${GREEN}OK:${NC}    $1"; }

echo "=============================="
echo "  Memex Lint — $(date +%Y-%m-%d)"
echo "=============================="
echo ""

# ── 1. Budget Check ──────────────────────────────────────────────
echo "── Budget Check ──"

# Budget includes: identity.md + active-threads (excluding _TEMPLATE.md) + patterns/*.md (excluding README.md) + inbox.md
BUDGET_FILES=()
BUDGET_FILES+=("$MEMEX_DIR/identity.md")
BUDGET_FILES+=("$MEMEX_DIR/inbox.md")

for f in "$MEMEX_DIR"/active-threads/*.md; do
    [[ "$(basename "$f")" == "_TEMPLATE.md" ]] && continue
    BUDGET_FILES+=("$f")
done

for f in "$MEMEX_DIR"/patterns/*.md; do
    [[ "$(basename "$f")" == "README.md" ]] && continue
    BUDGET_FILES+=("$f")
done

TOTAL_LINES=0
for f in "${BUDGET_FILES[@]}"; do
    lines=$(wc -l < "$f" 2>/dev/null || echo 0)
    TOTAL_LINES=$((TOTAL_LINES + lines))
done

BUDGET=400
if [ "$TOTAL_LINES" -gt "$BUDGET" ]; then
    error "Always-loaded budget: $TOTAL_LINES / $BUDGET lines (OVER by $((TOTAL_LINES - BUDGET)))"
else
    ok "Always-loaded budget: $TOTAL_LINES / $BUDGET lines ($((BUDGET - TOTAL_LINES)) headroom)"
fi

# Constitution line count (informational, not budgeted)
CONST_LINES=$(wc -l < "$REPO_ROOT/constitution.md" 2>/dev/null || echo 0)
echo "     Constitution: $CONST_LINES lines (budget-exempt)"
echo ""

# ── 2. Thread Size Check ─────────────────────────────────────────
echo "── Thread Size Check (active threads > 60 lines) ──"

SPLIT_THRESHOLD=60
for f in "$MEMEX_DIR"/active-threads/*.md; do
    [[ "$(basename "$f")" == "_TEMPLATE.md" ]] && continue
    lines=$(wc -l < "$f")
    name=$(basename "$f")
    if [ "$lines" -gt "$SPLIT_THRESHOLD" ]; then
        warn "$name: $lines lines — evaluate for split or compression"
    else
        ok "$name: $lines lines"
    fi
done
echo ""

# ── 3. Frontmatter Check ─────────────────────────────────────────
echo "── Frontmatter Check ──"

ALL_THREADS=()
for f in "$MEMEX_DIR"/active-threads/*.md "$MEMEX_DIR"/threads/*.md; do
    [[ "$(basename "$f")" == "_TEMPLATE.md" ]] && continue
    [ -f "$f" ] && ALL_THREADS+=("$f")
done

for f in "${ALL_THREADS[@]}"; do
    name=$(basename "$f")

    if ! grep -q "^last-touched:" "$f"; then
        error "$name: missing last-touched"
    fi
    if ! grep -q "^category:" "$f"; then
        error "$name: missing category"
    fi
    if ! grep -q "^hits:" "$f"; then
        error "$name: missing hits"
    fi
    if ! grep -q "^tags:" "$f"; then
        error "$name: missing tags"
    fi
done

# Check for valid categories
VALID_CATEGORIES="mathematics|cognition|systems|ventures|economics|civic"
for f in "${ALL_THREADS[@]}"; do
    name=$(basename "$f")
    cat_line=$(grep "^category:" "$f" 2>/dev/null || echo "")
    if [ -n "$cat_line" ]; then
        cat_value=$(echo "$cat_line" | sed 's/^category: *//')
        if ! echo "$cat_value" | grep -qE "^($VALID_CATEGORIES)$"; then
            error "$name: invalid category '$cat_value'"
        fi
    fi
done

ok "Frontmatter check complete"
echo ""

# ── 4. Summary Check ─────────────────────────────────────────────
echo "── Summary Check ──"

for f in "${ALL_THREADS[@]}"; do
    name=$(basename "$f")
    if ! grep -q "^## Summary" "$f"; then
        error "$name: missing ## Summary section"
    fi
done

ok "Summary check complete"
echo ""

# ── 5. Cross-Reference Integrity ─────────────────────────────────
echo "── Cross-Reference Integrity ──"

for f in "${ALL_THREADS[@]}"; do
    name=$(basename "$f")
    dir=$(dirname "$f")

    # Extract markdown links: [text](path.md)
    grep -oE '\[([^]]+)\]\(([^)]+\.md)\)' "$f" 2>/dev/null | while read -r match; do
        link_path=$(echo "$match" | grep -oE '\(([^)]+)\)' | tr -d '()')

        # Skip external URLs
        [[ "$link_path" == http* ]] && continue

        # Resolve relative path
        resolved="$dir/$link_path"
        resolved=$(cd "$dir" 2>/dev/null && realpath -m "$link_path" 2>/dev/null || echo "$resolved")

        if [ ! -f "$resolved" ]; then
            error "$name: broken link → $link_path"
        fi
    done
done

ok "Cross-reference check complete"
echo ""

# ── 6. Orphan Check ──────────────────────────────────────────────
echo "── Orphan Check (threads with no inbound references) ──"

for f in "${ALL_THREADS[@]}"; do
    name=$(basename "$f")
    name_no_ext="${name%.md}"

    # Search all threads for references to this file
    inbound=$(grep -rl "$name" "$MEMEX_DIR"/active-threads/ "$MEMEX_DIR"/threads/ 2>/dev/null | grep -v "$f" | grep -v "_TEMPLATE.md" | wc -l)

    if [ "$inbound" -eq 0 ]; then
        warn "$name: no inbound references (potential orphan)"
    fi
done

echo ""

# ── 7. Active Thread Count ───────────────────────────────────────
echo "── Active Thread Count ──"

ACTIVE_COUNT=0
for f in "$MEMEX_DIR"/active-threads/*.md; do
    [[ "$(basename "$f")" == "_TEMPLATE.md" ]] && continue
    ((ACTIVE_COUNT++))
done

if [ "$ACTIVE_COUNT" -gt 8 ]; then
    error "Active threads: $ACTIVE_COUNT (max 8)"
elif [ "$ACTIVE_COUNT" -lt 3 ]; then
    warn "Active threads: $ACTIVE_COUNT (unusually low)"
else
    ok "Active threads: $ACTIVE_COUNT (target: 5-8)"
fi
echo ""

# ── Summary ──────────────────────────────────────────────────────
echo "=============================="
if [ "$ERRORS" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo -e "${GREEN}All checks passed.${NC}"
elif [ "$ERRORS" -eq 0 ]; then
    echo -e "${YELLOW}$WARNINGS warning(s), 0 errors.${NC}"
else
    echo -e "${RED}$ERRORS error(s), $WARNINGS warning(s).${NC}"
fi
echo "=============================="

exit $ERRORS
