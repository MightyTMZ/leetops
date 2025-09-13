"""
URL configuration for leetops project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from playground import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # LeetOps API endpoints
    path('api/companies/', views.CompanyListView.as_view(), name='company-list'),
    path('api/companies/<int:company_id>/', views.CompanyDetailView.as_view(), name='company-detail'),
    path('api/simulation/incident/generate/', views.GenerateIncidentView.as_view(), name='generate-incident'),
    path('api/simulation/incident/resolve/', views.ResolveIncidentView.as_view(), name='resolve-incident'),
    path('api/user/rating/', views.UserRatingView.as_view(), name='user-rating'),
    path('api/admin/initialize-companies/', views.initialize_companies, name='initialize-companies'),
    
    # Include djoser URLs for authentication
    re_path(r'^auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.jwt')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)