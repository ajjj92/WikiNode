import xmlrpc.client
from xmlrpc.client import Error
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import logging
import sys
import json

with xmlrpc.client.ServerProxy("http://0.0.0.0:8000/", allow_none=True) as proxy:
    print(proxy)
    try:
        start = str(sys.argv[1])
        end = str(sys.argv[2])
        result = proxy.dispatch(start,end)
        print(json.loads(result))
    except xmlrpc.client.Error as er:
        print("ERROR", er)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Exiting..")
        sys.exit(0)
    except Exception:
        print('ERROR')
        sys.exit(1)
