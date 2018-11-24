from oauth2_provider.views.generic import ProtectedResourceView
from django.http import JsonResponse

class ApiEndpoint(ProtectedResourceView):
    def get(self, request, *args, **kwargs):
        member = request.user.member
        response = JsonResponse({'email': member.email,
                                 'first_name': member.first_name,
                                 'last_name': member.last_name})
        return response
