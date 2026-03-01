#!/usr/bin/env bash
# AI Talent Tracker - Search and Update Script
# Uses web-search skill to find AI company personnel movements, then merges into events.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_FILE="$PROJECT_DIR/data/events.json"
RESULTS_DIR="/tmp/ai-talent-tracker"
mkdir -p "$RESULTS_DIR"

SEARCH_CMD="bash \"$SKILLS_ROOT/web-search/scripts/search.sh\""

echo "=== AI Talent Tracker - Daily Update ==="
echo "Time: $(date)"
echo ""

# Define search queries
QUERIES=(
  "AI company executive hire leave 2025 2026"
  "OpenAI Anthropic hire leave executive 2025 2026"
  "Google DeepMind xAI Meta AI hire departure 2025 2026"
  "AI startup founder CTO departure join 2025 2026"
  "left OpenAI joined Anthropic Google DeepMind 2025"
  "Mistral Cohere Perplexity hire executive talent 2025 2026"
  "AI人才 离职 加入 OpenAI Anthropic DeepMind 2025 2026"
  "DeepSeek 月之暗面 智谱 人事变动 高管 2025 2026"
)

# Run searches
for i in "${!QUERIES[@]}"; do
  query="${QUERIES[$i]}"
  output_file="$RESULTS_DIR/search_result_$i.md"
  echo "[$((i+1))/${#QUERIES[@]}] Searching: $query"

  bash "$SKILLS_ROOT/web-search/scripts/search.sh" "$query" 10 > "$output_file" 2>/dev/null || {
    echo "  Warning: search failed for query $((i+1)), skipping..."
    continue
  }

  echo "  -> Saved results to $output_file"
  sleep 2  # Be polite to search engines
done

echo ""
echo "=== Search complete. Results saved to $RESULTS_DIR ==="
echo "Run the parse script to merge results into events.json:"
echo "  python3 $SCRIPT_DIR/parse_results.py $RESULTS_DIR $DATA_FILE"
