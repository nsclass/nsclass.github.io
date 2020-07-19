---
layout: single
title: Python - using requests with retry
date: 2020-07-17 14:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - python
permalink: "2020/07/17/python-requests-retry"
---

The following example will show how to create a request session with retries.

```python
def create_session(retry, back_off):
    retry_strategy = Retry(
        total=retry,
        connect=retry,
        read=retry,
        backoff_factor=back_off,
        # status_forcelist=[429, 500, 502, 503, 504],
        # method_whitelist=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session
```

Calling API with a created session

```
session = create_session(3, 0.1)
url = f"https://{host_name}:{port}/api/test"
headers = {'Content-type': 'application/json'}
payload = r'{ "data": "payload test" }'
data = session.post(url,
                    verify=False,
                    headers=headers,
                    data=payload)
print(data.text)
```
