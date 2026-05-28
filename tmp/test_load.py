import sys, time
sys.path.insert(0, 'scripts')
print('step1: import')
from search_server import *
print('step2: load_data start')
t = time.time()
ok = load_data()
print(f'step3: done in {time.time()-t:.1f}s')
