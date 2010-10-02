# -*- coding: utf-8 -*-
#
#  views.py
#  simsearch
# 
#  Created by Lars Yencken on 30-08-2010.
#  Copyright 2010 Lars Yencken. All rights reserved.
#

"""
Views for the search app.
"""

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse

from cjktools import scripts

import models

def index(request):
    "Renders the search display."
    kanji = request.GET.get('kanji', '')
    kanji_ok = _is_kanji(kanji)

    if not kanji or not kanji_ok:
        # show the search dialog
        context = {
                'kanji': kanji,
                'kanji_ok': kanji_ok,
            }
        if kanji:
            context['error'] = 'Please enter a single kanji only as input.'
        return render_to_response('search/index.html', context,
                context_instance=RequestContext(request))

    # show the search plane instead

    # make sure the path is ok
    path = request.GET.get('path', '')
    if not all(map(_is_kanji, path)):
        path = []

    path = list(path) + [kanji]
    node = models.Node.objects.get(pivot=kanji)
    neighbours = [n.kanji for n in sorted(node.neighbours, reverse=True)]
    neighbours = neighbours[:settings.N_NEIGHBOURS_RECALLED]

    context = {'data': simplejson.dumps({
                    'kanji': kanji,
                    'tier1': neighbours[:4],
                    'tier2': neighbours[4:9],
                    'tier3': neighbours[9:],
                    'path': ''.join(path),
                })}
    return render_to_response('search/display.html', context,
            context_instance=RequestContext(request))

def translate(request, kanji=None):
    "Updates the query model before redirecting to the real translation."
    kanji = kanji or request.GET.get('kanji')
    if not _is_kanji(kanji):
        raise Http404

    path = request.GET.get('path')
    if path and len(path) > 1 and all(map(_is_kanji, path)) \
            and path.endswith(kanji):
        models.Node.update(path)
        models.Trace.log(request, path)

    return HttpResponseRedirect(reverse('translate_kanji', args=[kanji]))

def search_json(request, pivot=None):
    "Returns the search display data as JSON."
    pivot = pivot or request.GET.get('pivot')
    node = models.Node.objects.get(pivot=pivot)
    neighbours = [n.kanji for n in sorted(node.neighbours, reverse=True)]
    neighbours = neighbours[:settings.N_NEIGHBOURS_RECALLED]

    response_dict = {
                'pivot_kanji': pivot,
                'tier1': neighbours[:4],
                'tier2': neighbours[4:9],
                'tier3': neighbours[9:],
            }
    return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype='application/javascript',
        )

def _is_kanji(kanji):
    return isinstance(kanji, unicode) and len(kanji) == 1 \
            and scripts.script_type(kanji) == scripts.Script.Kanji

# vim: ts=4 sw=4 sts=4 et tw=78:
