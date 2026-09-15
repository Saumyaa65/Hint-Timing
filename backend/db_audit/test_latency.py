import os, sys, time, django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hint_system.settings')
django.setup()
from django.conf import settings
from langchain_openai import ChatOpenAI

models = [
    'meta-llama/llama-3.1-8b-instruct',
    'qwen/qwen-2.5-coder-32b-instruct',
    'deepseek/deepseek-chat',
    'meta-llama/llama-3.3-70b-instruct'
]

api_key = getattr(settings, 'OPENROUTER_API_KEY', None)

for m in models:
    t0 = time.time()
    try:
        llm = ChatOpenAI(model=m, openai_api_key=api_key, openai_api_base='https://openrouter.ai/api/v1', temperature=0.1, max_tokens=200, max_retries=0)
        res = llm.invoke('Hello, respond with JSON {"status": "ok"}.')
        dt = time.time() - t0
        print(f"[OK] {m} ({dt:.2f}s): {res.content[:60]}")
    except Exception as e:
        dt = time.time() - t0
        print(f"[FAIL] {m} ({dt:.2f}s): {e}")
