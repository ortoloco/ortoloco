from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required
def profile(request):
    member = request.user.member
    response = JsonResponse({'email': member.email,
                             'first_name': member.first_name,
                             'last_name': member.last_name})
    return response
