#!/bin/bash
# This script helps identify sections that need translation
echo "Scanning for hard-coded English text in index.html..."
grep -n "Search intents\|Intent Name\|Description\|Trigger Phrases\|Action Type\|Add New Intent" index.html | head -20
