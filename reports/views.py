#!/usr/bin/env python

from collections import OrderedDict
import json

from clan.utils import GLOBAL_ARGUMENTS
from django.shortcuts import render

import app_config
from reports import models

def index(request):
    """
    Project index.
    """
    context = {
        'projects': models.Project.objects.all()    
    }

    return render(request, 'index.html', context)

def project(request, slug):
    """
    Project report index.
    """
    obj = models.Project.objects.get(slug=slug)

    context = {
        'project': obj, 
        'reports': obj.reports.exclude(last_run__isnull=True)
    }

    return render(request, 'project.html', context)

def report(request, slug, ndays):
    """
    Generate a project report.
    """
    obj = models.Report.objects.get(
        project__slug=slug,
        ndays=ndays
    )

    data = json.loads(obj.results_json)

    global_args = OrderedDict()

    for arg in GLOBAL_ARGUMENTS:
        if data[arg] is not None:
            global_args[arg] = data[arg]

    context = {
        'global_args': global_args,
        'report': obj 
    }

    return render(request, 'report.html', context)

def compare_query(request):
    """
    Compare results of a query.
    """
    context= {
        'queries': models.Query.objects.all(),
        'report_ndays': app_config.DEFAULT_REPORT_NDAYS,
    }

    query_slug = request.GET.get('query', None)
    ndays = request.GET.get('ndays', None)
    unit = request.GET.get('unit', 'count')

    if query_slug and ndays:
        query = models.Query.objects.get(slug=query_slug)
        query_results = models.QueryResult.objects.filter(
            query=query,
            report_ndays=ndays
        )

        projects = []
        results = OrderedDict()

        # Build comparison table
        for qr in query_results:
            project = qr.report.project
            projects.append(project)

            for metric in qr.metrics.all():
                if metric.name not in results:
                    results[metric.name] = OrderedDict()

                for dimension in metric.dimensions.all():
                    if dimension.name not in results[metric.name]:
                        results[metric.name][dimension.name] = []

                    results[metric.name][dimension.name].append(dimension)

        context.update({
            'query': query,
            'ndays': int(ndays),
            'unit': unit,
            'projects': projects,
            'results': results
        })

    return render(request, 'compare_query.html', context)
