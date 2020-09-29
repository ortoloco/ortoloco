from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.generic.base import View
from django.shortcuts import render
from django.core import management
from django.utils import timezone

class Custom500View(View):
    def dispatch(self, request, *args, **kwargs):
        return render(request, '500.html', {}, status=500)
        

def error(request):
    asdf

def date(request):
    response = JsonResponse({'date': timezone.now().date()})
    return response


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
    membergroups = request.user.groups.values_list('name',flat = True)
    grouplist = list(membergroups)
    response = JsonResponse({'id': member.id,
                             'email': member.email,
                             'firstName': member.first_name,
                             'lastName': member.last_name,
                             'displayName': member.first_name + " " + member.last_name,
                             'roles': grouplist})
    return response

@login_required
def openid_init(request):
    response = management.call_command("creatersakey")
    return response
