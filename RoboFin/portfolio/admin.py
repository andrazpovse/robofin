from django.contrib import admin
from .models import Asset, Portfolio, PortfolioAsset

# Register your models here.
admin.site.register(Asset)
admin.site.register(Portfolio)
admin.site.register(PortfolioAsset)