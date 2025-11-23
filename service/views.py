from django.http import HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.views.generic import TemplateView,ListView
#httpresponse
def display(request):
      return HttpResponse("this my first wevb")
