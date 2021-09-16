<img src="images/logo.png" alt="logo" width="100%"/>

# RoboFin
RoboFin is a robo financial advisor, that takes care of investments for you. Based on your risk profile, it automatically assigns you a portfolio, tailored to fit your needs. Aside from classic financial instruments such as equities, bonds and commodities, RoboFin also allocates into five largest cryptocurrencies (BTC, ETH, ADA, BNB and XRP).

# Launch RoboFin in Docker
We have made the application easy to run and preview using Docker.
Build and run the docker image by running the following command inside the root of the project.

    docker-compose up

The application should be up and running on:

    http://localhost:8000


## Existing users
We have added some predefined users, so you can view different risk profiles.
The users we have created have very low (10), low (20), medium (30), high (45), very high (60) and extreme (63) risk profiles.

| Username   |      Password      |  Risk profile |
|----------|-------------|------|
| john_very_low |  robofin1 | Very Low (10) |
| mary_low |  robofin1 | Low (20) |
| frank_medium |  robofin1 | Medium (30) |
| linda_high |  robofin1 | High (45) |
| eli_very_high |  robofin1 | Very High (60) |
| bob_extreme |  robofin1 | Extreme (63) |



# Setting up Python environment for development
```
python3 -m venv env
source /env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```