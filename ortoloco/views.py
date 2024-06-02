from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.generic.base import View
from django.shortcuts import render
from django.contrib.auth.decorators import permission_required

from juntagrico.util.pdf import return_pdf_http


class Custom500View(View):
    def dispatch(self, request, *args, **kwargs):
        return render(request, '500.html', {}, status=500)


@login_required
def nextcloud_profile(request):
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

@permission_required('juntagrico.can_view_lists')
def tour_overview(request):
    return return_pdf_http('tour_overview.pdf')

@permission_required('juntagrico.can_view_lists')
def tour_list(request):
    return return_pdf_http('tour_list.pdf')
