from django.shortcuts import render,redirect
import logging
import datetime

logger = logging.getLogger(__name__)


def index_view(request):
    return render(request,'index.html')