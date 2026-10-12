from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Server-side guard for every management view.

    Anonymous visitors are redirected to the management login page.
    Signed-in users without staff status receive a 403 response.
    """

    def test_func(self):
        user = self.request.user
        return user.is_active and user.is_staff
