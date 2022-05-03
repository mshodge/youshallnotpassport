# youshallnotpass

![youshallnotpass](https://media.giphy.com/media/njYrp176NQsHS/giphy-downsized-large.gif)

A simple `requests` script to check whether the following [UK Passport](https://www.gov.uk/apply-renew-passport) services are available:

- [Premium](https://www.gov.uk/get-a-passport-urgently/online-premium-service)
- [1 week fast track](https://www.gov.uk/get-a-passport-urgently/1-week-fast-track-service)

## Get

- `git clone https://github.com/mshodge/youshallnotpassport.git`

## Set

- `pip install -r requirements.txt`

## Go

`python main.py`

## Additional

### Twitter

If you want to post to Twitter. You will need elevated v1 access on the Twitter Developer site. Then create a
file called `twitter_credentials.py` in `/config/` with the following:

```
consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""
```

Change the `post_to_twitter` to be `True` in `main.py`. If running locally change `github_action` to `False`.

### Proxy

Add proxy settings to a `proxies.py` file in `/config/` if you require them.

Change the `proxy` to be `True` in `main.py`.
