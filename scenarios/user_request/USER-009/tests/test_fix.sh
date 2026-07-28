#!/bin/bash
# Fix verification test for USER-009
# Exits 0 if fix is applied correctly.

set -e

# Check: ui_text_updated
if grep -q '<button>Guardar cambios</button>' var/www/templates/settings.html && grep -q '<a>Cancelar</a>' var/www/templates/settings.html && ! grep -q 'Save changes\|>Cancel<' var/www/templates/settings.html; then
    echo "PASS: ui_text_updated"
else
    echo "FAIL: ui_text_updated"
    exit 1
fi

exit 0
