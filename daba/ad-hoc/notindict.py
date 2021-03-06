#!/usr/bin/env python3
from bamana import test
from orthography import *
from morphology import *

for w in test.words():
    res = convertw(w)
    wordindict = False
    for r in res:
        if not orth_compliant(r):
            break
        if lemmatize(r):
            wordindict =True
    else:
        if not wordindict:
            print(" ".join(res))


