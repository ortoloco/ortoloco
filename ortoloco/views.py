from django.http import JsonResponse
from django.views.generic.base import View
from django.shortcuts import render
from oauth2_provider.decorators import protected_resource


class Custom500View(View):
    def dispatch(self, request, *args, **kwargs):
        return render(request, '500.html', {}, status=500)


@protected_resource(scopes=['nextcloud'])
def nextcloud_profile(request):
    user = request.resource_owner
    member = user.member
    membergroups = user.groups.values_list('name',flat = True)
    grouplist = list(membergroups)
    response = JsonResponse({'id': member.id,
                             'email': member.email,
                             'firstName': member.first_name,
                             'lastName': member.last_name,
                             'displayName': member.first_name + " " + member.last_name,
                             'roles': grouplist})
    return response
