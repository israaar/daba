#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import formats
from orthography import detone

infile = sys.argv[1]

reader = formats.HtmlReader(infile)

print "<doc ",
print u'id="{0}"'.format(os.path.basename(infile)).encode('utf-8'),
metad = dict(reader.metadata)
try:
    genres = metad['text:genre'].split(';')
    hgenres = [g.split(' : ')[0] for g in genres] + genres
    hgenres.sort()
    metad['text:genre'] = u';'.join(hgenres)
    print u'text_genre="{0}"'.format(metad['text:genre']).encode('utf-8'),
except (KeyError):
    print 'text_genre="UNDEF"',
try:
    print u'text_title="{0}"'.format(metad['text:title']).encode('utf-8'),
except (KeyError):
    print 'text_title="UNDEF"',
print ">"

for par in reader.glosses:
    print "<p>"
    for sent,annot in par:
        print "<s>"
        #print u'<sent source="{0}">'.format(sent).encode('utf-8')
        for token in annot:
            gt = formats.GlossToken(token)
            print u"{0}\t".format(gt.token).encode('utf-8'),
            if gt.type == 'w':
                print u"\t".join([u'|'.join(filter(None, set(s))) for s in zip(*[(g.form, '|'.join(g.ps), g.gloss) for g in gt.glosslist])]).encode('utf-8'),
                print u"\t{0}".format(u'|'.join(filter(None, set([detone(g.form).lower() for g in gt.glosslist])))).encode('utf-8')
            else:
                print u"\t".join([gt.token, gt.type, gt.token, gt.token]).encode('utf-8')
        print "</s>"
    print "</p>"

print "</doc>"



