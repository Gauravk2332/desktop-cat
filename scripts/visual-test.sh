#!/bin/bash
# scripts/visual-test.sh — Run visual QA for desktop-cat in Hermes Docker container
# Usage: bash scripts/visual-test.sh [capture-all|compare-all|generate-baselines]

set -e

PROJECT_DIR="/root/.openclaw/home-mira/desktop-cat"
HERMES_CONTAINER="hermes"
TEMP_DIR="/tmp/test-cat"
COMMAND="${1:-capture-all}"

echo "=== Desktop Cat Visual Test: $COMMAND ==="

# 1. Sync project files to Hermes
echo "Syncing project to Hermes..."
docker cp "$PROJECT_DIR" "$HERMES_CONTAINER:$TEMP_DIR" 2>/dev/null || {
    docker exec "$HERMES_CONTAINER" mkdir -p "$TEMP_DIR"
    docker cp "$PROJECT_DIR/." "$HERMES_CONTAINER:$TEMP_DIR/"
}

# 2. Ensure Xvfb is running
docker exec "$HERMES_CONTAINER" bash -c 'pgrep Xvfb || (nohup Xvfb :99 -screen 0 1920x1080x24 -ac > /dev/null 2>&1 & sleep 1)'

# 3. Run visual test
echo "Running visual test: $COMMAND..."
docker exec -e DISPLAY=:99 "$HERMES_CONTAINER" bash -c "cd $TEMP_DIR && python tests/visual_test.py $COMMAND"

# 4. Copy results back
echo "Copying screenshots back..."
docker exec "$HERMES_CONTAINER" bash -c "mkdir -p $TEMP_DIR/tests/screenshots"
docker cp "$HERMES_CONTAINER:$TEMP_DIR/tests/screenshots/." "$PROJECT_DIR/tests/screenshots/"

# 5. Generate timestamp report
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "Test run $TIMESTAMP" > "$PROJECT_DIR/tests/screenshots/report_$TIMESTAMP.txt"

echo "=== Done ==="
echo "Screenshots: tests/screenshots/"
echo "=============="
