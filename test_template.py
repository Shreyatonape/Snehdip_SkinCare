import sys
sys.path.append('.')
from app import app
from flask import render_template

with app.app_context():
    try:
        # Test rendering patient_chat.html
        result = render_template('patient_chat.html')
        print('✅ patient_chat.html renders successfully')
        print(f'✅ Template length: {len(result)} characters')

        # Check for any remaining Jinja syntax
        if '{%' in result or '%}' in result:
            print('❌ WARNING: Jinja syntax still found in template')
        else:
            print('✅ No Jinja syntax found in rendered template')

    except Exception as e:
        print(f'❌ ERROR rendering template: {e}')