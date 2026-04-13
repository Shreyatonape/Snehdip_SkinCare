import sys
sys.path.append('.')
from app import app
from flask import render_template
import re

with app.app_context():
    try:
        # Read the template file directly to check for Jinja syntax
        with open('templates/patient_chat.html', 'r') as f:
            template_content = f.read()

        print('=== Template Content Analysis ===')

        # Check for Jinja syntax patterns
        jinja_patterns = [
            r'\{\%\s*extends\s*.*?\%\}',
            r'\{\%\s*block\s*.*?\%\}',
            r'\{\%\s*endblock\s*\%\}',
            r'\{\%\s*if\s*.*?\%\}',
            r'\{\%\s*endif\s*\%\}',
            r'\{\{\s*.*?\s*\}\}'
        ]

        found_jinja = False
        for pattern in jinja_patterns:
            matches = re.findall(pattern, template_content)
            if matches:
                print(f'❌ Found Jinja syntax: {pattern}')
                print(f'   Matches: {matches}')
                found_jinja = True

        if not found_jinja:
            print('✅ No Jinja syntax found in template')

        # Check basic HTML structure
        if '<!DOCTYPE html>' in template_content:
            print('✅ Valid HTML DOCTYPE found')

        if '<html' in template_content and '</html>' in template_content:
            print('✅ Valid HTML structure found')

        if '<head>' in template_content and '<body>' in template_content:
            print('✅ Head and body sections found')

        print('\n=== Template Structure ===')
        lines = template_content.split('\n')
        print(f'First line: {lines[0]}')
        print(f'Last line: {lines[-1]}')
        print(f'Total lines: {len(lines)}')

    except Exception as e:
        print(f'❌ ERROR analyzing template: {e}')