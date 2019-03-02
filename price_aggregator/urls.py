"""price_aggregator URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include

import price_aggregator.views as views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.IndexView.as_view()),

    path('price/<str:currency_code>', views.PriceView.as_view(), name='price'),
    path('currency/choose/<str:path>', views.CurrencyChooseView.as_view(), name='currency_choose'),
    path('price/<str:currency_code>/<str:date_time>', views.SpotPriceView.as_view(), name='spot_price'),
    path('movement/<str:currency_code>', views.PriceChangesView.as_view(), name='price'),
    path('currencies', views.CurrenciesView.as_view(), name='currencies'),
    path('providers', views.ProvidersView.as_view(), name='providers'),
    path('provider/choose/<str:path>', views.ProviderChooseView.as_view(), name='provider_choose'),
    path('provider/<str:provider>', views.ProviderResponsesView.as_view(), name='provider'),
    path('provider/<str:provider>/price/<str:currency_code>', views.ProviderPriceView.as_view(), name='provider'),
    path(
        'provider/<str:provider>/price/<str:currency_code>/<str:date_time>',
        views.ProviderSpotPriceView.as_view(),
        name='provider_spot_price'
    )
]
