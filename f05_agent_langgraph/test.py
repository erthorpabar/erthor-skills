import requests
response = requests.get("https://api.ttt.ss/v1/models", 
    headers={"Authorization": "Bearer sk-4FBqRwNEz34fac5kVjDh61LSruLwq6adUo7Uno23v3jyCpia"})
print(response.status_code, response.text)