"""
Impersonation (django-impersonate, settings.IMPERSONATE and ortoloco.middleware.AdminImpersonateMiddleware):
- members of the group "impersonators" may impersonate
- superusers may impersonate everybody, all others only unprivileged users (juntagrico.defaults.unprivileged_only)
- in the admin (/admin/) only superusers impersonate, everybody else stays themselves
"""
from django.contrib.auth.models import Group, Permission
from django.urls import reverse

from ortoloco.tests import OrtolocoTestCase


class ImpersonateTests(OrtolocoTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        impersonators = Group.objects.create(name='impersonators')
        # superuser impersonating
        cls.superuser = cls.create_member('superuser@example.org').user
        cls.superuser.is_superuser = cls.superuser.is_staff = True
        cls.superuser.save()
        cls.superuser.groups.add(impersonators)
        # staff member impersonating, may use the admin
        cls.impersonator = cls.create_member('impersonator@example.org').user
        cls.impersonator.is_staff = True
        cls.impersonator.save()
        cls.impersonator.groups.add(impersonators)
        cls.impersonator.user_permissions.add(Permission.objects.get(codename='view_member'))
        # staff member without impersonation rights, only superusers may impersonate them
        cls.staff = cls.create_member('staff@example.org').user
        cls.staff.is_staff = True
        cls.staff.save()
        cls.staff.user_permissions.add(Permission.objects.get(codename='view_subscription'))
        # unprivileged member
        cls.unprivileged = cls.create_member('unprivileged@example.org').user

    def impersonate(self, impersonator, user):
        self.client.force_login(impersonator)
        self.client.get(reverse('impersonate-start', args=[user.pk]))

    def user_of(self, url):
        return self.client.get(url).wsgi_request.user

    def test_superuser_impersonates_in_admin(self):
        self.impersonate(self.superuser, self.staff)
        self.assertEqual(self.user_of('/admin/'), self.staff)
        self.assertEqual(self.user_of('/my/profile'), self.staff)
        # the admin as the staff member sees it
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'href="/admin/auth/user/"')

    def test_impersonator_stays_themselves_in_admin(self):
        self.impersonate(self.impersonator, self.unprivileged)
        self.assertEqual(self.user_of('/my/profile'), self.unprivileged)
        self.assertEqual(self.user_of('/admin/'), self.impersonator)
        self.assertEqual(self.client.get('/admin/').status_code, 200)

    def test_impersonator_only_unprivileged(self):
        self.impersonate(self.impersonator, self.staff)
        self.assertEqual(self.user_of('/my/profile'), self.impersonator)
        self.assertEqual(self.user_of('/admin/'), self.impersonator)

    def test_group_required(self):
        self.impersonate(self.staff, self.unprivileged)
        self.assertEqual(self.user_of('/my/profile'), self.staff)

    def test_stop(self):
        self.impersonate(self.superuser, self.staff)
        self.client.get(reverse('impersonate-stop'))
        self.assertEqual(self.user_of('/admin/'), self.superuser)
