# BasicUrlscanPy
A very, very simple base Python class to use with urlscan.io

# Background

I found myself essentially writing the same code over and over for talking to urlscan.io for various projects and opted to stop reinventing the wheel and create a very simple base class that I can reuse and change to fit whatever task it is I am trying to do. This class has one job and one job only - make the appropriate call to urlscan.io with the right headers and either return `None` if something explodes along the way or a `requests.Response` object (see [Requests Documentation](https://requests.readthedocs.io/en/latest/) for more details). It does not concern itself with how that `Response` is handled; that gets done elsewhere by whatever chooses to subclass this. I just wanted to abstract out the easiest possible bits.

# FAQ

## Why does this not meet insert some Python coding standard here?

I am not a super coder. My tasks are usually slapping something together to do a job in the short term or creating a proof of concept that can be handed off to someone infinitely more talented than myself to make into better code. Having said that, I am learning how to write better code, and feedback or PRs on this to point me in the right direction are very much appreciated.

## Why does this not have insert some urlscan.io Pro API call here?

In keeping with the urlscan.io terms that request not to divulge the Pro account features publicly, I have not added them to this very basic class. I do, however, have a "Pro Basic" class that does extend this class with the Pro calls and can provide some feedback on how it can be done if requested.

## Why does this not use async?

As above, I am not a super skilled Python coder and have yet to fully get to grips with async and its best use cases. If you think it should be used here and can explain it, I again would very much appreciate it and be happy to make the changes required.

## Aren't there better examples than this?

Very likely yes, but I found many of them were "feature complete" and often overcomplicated what I was trying to do and would require changes each time, so I wanted to strip it back to the really simple stuff. Some of the logic in this class does take inspiration from other code, however.

## Does this need a urlscan.io API key?

It does not, but I recommend that you use one in any case (you can get yourself a free urlscan.io account) as it will typically give you a better experience. Notably, the ability to POST scans via the API requires an API key.

# Usage options

The class has some very basic arguments that you don't need to provide for it to work, but you should consider:

* `api_key` - the urlscan.io API key that you can get from within your account.
* `user_agent` - the user agent string `requests` will set in the headers. If not provided, it will default to `BasicUrlscanPy/v1`, but it is best practice to set your own user agent.
* `retries` - the number of times the `requests` library will retry a call before giving up. Default is `5`.
* `backoff` - this sets the backoff factor that `requests` uses to determine the time between the next attempt. This exponentially grows per attempt. Default is `1`.

# Really simple usage

```python
from base import BaseUrlscan
urlscan = BaseUrlscan()
urlscan_quota = urlscan.get_quotas()
urlscan_result = urlscan.get_result(result_uuid='0195e0c6-af9a-7000-997c-0e0c32811406')
search_query = {'q': 'page.domain:example.com'}
urlscan_search = urlscan.get_search(params=search_query)
scan_request = {'url': 'https://example.com'}
urlscan_scan = urlscan.post_scan(payload=scan_request)
```

If something exploded trying to talk to urlscan.io, then `urlscan_quota`, `urlscan_result`, `urlscan_search`, or `urlscan_scan` will return `None`. If it did manage to talk to the service, you will be provided a `requests.Response` object that you can interact with in a variety of ways depending on your use cases. This could include checking whether you got the response code you expected, actioning the response text/JSON, or some other item. That's entirely up to you; this very basic class does not go into that detail.