import os
import sys
import json
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hint_system.settings')

import django
django.setup()

from langchain_openai import ChatOpenAI
from django.conf import settings

api_key = settings.OPENROUTER_API_KEY

res = json.loads(urllib.request.urlopen('https://openrouter.ai/api/v1/models').read())
free_models = [m['id'] for m in res.get('data', []) if float(m.get('pricing', {}).get('prompt', '1')) == 0]

print(f"Testing {len(free_models)} free models...", flush=True)
working_models = []

for m in free_models:
    try:
        print(f"Testing {m}...", flush=True)
        llm = ChatOpenAI(
            model=m,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            max_tokens=100
        )
        out = llm.invoke('Return JSON: {"status": "OK"}').content
        print(f"SUCCESS {m}: {out[:100]}", flush=True)
        working_models.append(m)
        if len(working_models) >= 5:
            break
    except Exception as e:
        print(f"FAIL {m}: {str(e)[:150]}", flush=True)

print("WORKING FREE MODELS:", working_models, flush=True)
