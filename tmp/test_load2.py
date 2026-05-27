import sys, time
sys.path.insert(0, 'scripts')
sys.stdout.flush()
print('A', flush=True)
import jieba  
print('B', flush=True)
from search_server import load_data
print('C', flush=True)
try:
    load_data()
    print('D', flush=True)
except Exception as e:
    print(f'ERR: {e}', flush=True)
