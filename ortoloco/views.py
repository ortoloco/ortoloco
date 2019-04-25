from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.generic.base import View
from django.shortcuts import render

class Custom500View(View):
    def dispatch(request):
        return render(request, '500.html', {}, status=500)
        

def error(request):
    asdf


@login_required
def politoloco_profile(request):
    member = request.user.member
    response = JsonResponse({'email': member.email,
                             'first_name': member.first_name,
                             'last_name': member.last_name})
    return response


@login_required
def beipackzettel_profile(request):
    member = request.user.member
    response = JsonResponse({'identifier': member.email,
                             'email': member.email,
                             'firstName': member.first_name,
                             'lastName': member.last_name})
    return response
