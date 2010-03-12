from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import string_concat, ugettext as _
from django.contrib import messages
import logging

try:
    import reportlab
    from reportlab.graphics.shapes import Drawing              
    from reportlab.lib import colors
    from reportlab.graphics.charts.piecharts import Pie, Pie3d
except ImportError:
    reportlab = None

from projector.models import Task, Status

def task_reports(request, template_name='projector/task/reports.html'):
    """
    Task reports view.
    """
    #task_list = Task.objects.all()
    return get_actual_status_img(request)

def get_actual_status_img(request, output_format='png', width=600, height=600):
    if reportlab is None:
        messages.error(request, _("Module") + " reportlab " + _("is not available"))
        try:
            redirect_to = request.META['HTTP_REFERER']
        except KeyError:
            redirect_to = '/'
        return HttpResponseRedirect(redirect_to)
    status_list = Status.objects.all()
    
    drawing = Drawing(width, height)
    pie = Pie3d()
    pie.x = 100
    pie.y = 100
    pie.width = width / 2
    pie.height = height / 2

    pie.labels = [ s.name for s in status_list ]
    pie.data = [ s.task_set.count() for s in status_list ]
    pie.slices[3].fontColor = colors.red
    pie.slices[0].fillColor = colors.darkcyan
    pie.slices[1].fillColor = colors.blueviolet
    pie.slices[2].fillColor = colors.blue
    pie.slices[3].fillColor = colors.cyan
    pie.slices[4].fillColor = colors.aquamarine
    pie.slices[5].fillColor = colors.cadetblue
    pie.slices[6].fillColor = colors.lightcoral
        
    drawing.add(pie)
    image = drawing.asString(output_format)
    response = HttpResponse(image, mimetype='image/%s' % output_format.lower())
    return response
