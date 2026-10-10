#!/usr/bin/env python3
import inspect, ccobra.syllogistic as syll
for name in ["encode_task","encode_response","decode_response"]:
    obj=getattr(syll,name)
    print(f"\n===== {name} =====")
    print(inspect.getsource(obj))