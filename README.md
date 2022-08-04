# youshallnotpassport

![youshallnotpassport](https://media.giphy.com/media/njYrp176NQsHS/giphy-downsized-large.gif)

This is the code-based behind the Twitter account [@ukpassportcheck](https://twitter.com/ukpassportcheck). 
Nothing is hidden. I code in the open. You can see all the code here and select `Actions` tab 
to see the GitHub Actions in progress.

The code is split into two parts - both use the Python package `tweepy` to post to Twitter:

#### Status check
A simple `requests` script to check whether the following [UK Passport](https://www.gov.uk/apply-renew-passport) services are available:

- [Premium](https://www.gov.uk/get-a-passport-urgently/online-premium-service)
- [1 week fast track](https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service)

#### Appointments table check
Uses the Python package `selenium` to get the appointments table when the service is online. Then
keeps checking and posts again if more appointments are added.

## Using the code

### Get

>`git clone https://github.com/mshodge/youshallnotpassport.git`

### Set

>`pip install -r requirements.txt`

### Go

### Status check

>`python main.py`

### Appointments table check

#### Fast Track

>`python find_appointments_fast_track.py`

#### Premium

>`python find_appointments_premium.py`

### Configuration

#### Twitter

To post to Twitter you will need elevated v1 access on the Twitter Developer site. Then create a
file called `twitter_credentials.py` in `/config/` with the following:

```
consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""
```

#### Proxy

Add proxy settings to a `proxies.py` file in `/config/` if you require them.

Change the `is_proxy` to be `True` in `main.py`.
