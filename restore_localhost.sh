#!/bin/bash

# SpeakSense - Restore Localhost Configuration
# This script restores the original localhost configuration in portal files

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Restoring localhost configuration..."

# Restore portal files if backups exist
if [ -f "$PROJECT_ROOT/portal/assets/js/app.js.original" ]; then
    cp "$PROJECT_ROOT/portal/assets/js/app.js.original" "$PROJECT_ROOT/portal/assets/js/app.js"
    echo "✓ Admin portal restored to localhost"
fi

if [ -f "$PROJECT_ROOT/web/index.html.original" ]; then
    cp "$PROJECT_ROOT/web/index.html.original" "$PROJECT_ROOT/web/index.html"
    echo "✓ Testing portal restored to localhost"
fi

echo "Done! Original localhost configuration restored."
