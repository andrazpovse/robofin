from django.db import models

class Asset(models.Model):
    name = models.CharField(max_length=50)
    historical_prices = models.TextField(verbose_name="Historical Prices CSV")

    def __str__(self):
        return self.name

class Portfolio(models.Model):
    name = models.CharField(max_length=255)
    assets = models.ManyToManyField(
        Asset,
        through='PortfolioAsset'
    )
    
    asset_tickers = models.TextField()
    metrics = models.TextField(verbose_name="Portfolio Metrics")
    risk_score = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return "{name} with assets: {assets}".format(name=self.name, assets=",".join([asset.name for asset in self.assets.all()]))

class PortfolioAsset(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    allocation = models.DecimalField(max_digits=4, decimal_places=3)

    def __str__(self):
        return "{asset} : {allocation}%".format(allocation=self.allocation*100, asset=self.asset.name)

