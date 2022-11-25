from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from oneid.views import LoginView, GetUser, OneIDLoginView, Logout

urlpatterns = [
    path('oneid-login', csrf_exempt(OneIDLoginView.as_view()), name='oneid_login'),
    path('login', csrf_exempt(LoginView.as_view()), name='login'),
    path('get-user', csrf_exempt(GetUser.as_view()), name='user_data'),
    path('logout', csrf_exempt(Logout.as_view()), name='logout')
]
