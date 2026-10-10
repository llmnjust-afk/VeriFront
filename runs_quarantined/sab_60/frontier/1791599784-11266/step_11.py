#!/usr/bin/env python3
import inspect
try:
    import ccobra
    print("ccobra imported", ccobra)
    import ccobra.syllogistic as syll
    print("syll module", syll)
    print("dir", [x for x in dir(syll) if not x.startswith("_")])
    if hasattr(syll, "Syllogism"):
        print(inspect.getsource(syll.Syllogism)[:4000])
    for name in ["encode_task","decode_response","encode_response"]:
        if hasattr(syll, name):
            print("\n", name)
            print(inspect.getsource(getattr(syll,name))[:3000])
except Exception as e:
    print("ERR", repr(e))