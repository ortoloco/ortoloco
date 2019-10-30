from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.generic.base import View
from django.shortcuts import render

class Custom500View(View):
    def dispatch(self, request, *args, **kwargs):
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
    membergroups = request.user.groups.values_list('name',flat = True)
    grouplist = list(membergroups)
    response = JsonResponse({'id': member.id,
                             'email': member.email,
                             'firstName': member.first_name,
                             'lastName': member.last_name,
                             'displayName': member.first_name + " " + member.last_name,
                             'roles': grouplist})
    return response
