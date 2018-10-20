# coding: utf-8
import requests
url = '' # Need hook to push to slack
data = {"text":"Hello, World!"}
requests.post(url,json=data)
