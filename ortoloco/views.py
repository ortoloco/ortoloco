from django.http import HttpResponse
from django.views.generic.base import View
from django.shortcuts import render

class Custom500View(View):
    def dispatch(self, request, *args, **kwargs):
        return render(request, '500.html', {}, status=500)
        

def error(request):
    asdf