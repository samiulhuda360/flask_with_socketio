import requests
import base64


proxies = {
    "http": "http://letezcbn-rotate:6792gwkuo8oo@p.webshare.io:80/",
    "https": "http://letezcbn-rotate:6792gwkuo8oo@p.webshare.io:80/"
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8,es;q=0.7',
}

# Function to post content to WordPress site
def test_post_to_wordpress(site_url, username, app_password, content):
    url_json = f"https://{site_url}/wp-json/wp/v2/posts"
    credentials = f"{username}:{app_password}"
    token = base64.b64encode(credentials.encode())
    auth_headers = {'Authorization': 'Basic ' + token.decode('utf-8')}
    data = {
        "title": "Test Post from API",
        "content": content,
        "status": "publish"
    }
    headers.update(auth_headers)  # Merge headers with authorization headers

    try:
        response = requests.post(url_json, headers=headers, json=data, proxies=proxies)
        return response.text
    except requests.exceptions.ConnectionError:
        return None  # Or return an appropriate response indicating a connection error

def delete_from_wordpress(site_url, username, app_password, post_id):
    url_json = f"https://{site_url}/wp-json/wp/v2/posts/{post_id}"
    credentials = f"{username}:{app_password}"
    token = base64.b64encode(credentials.encode())
    auth_headers = {'Authorization': 'Basic ' + token.decode('utf-8')}
    headers.update(auth_headers)  # Merge headers with authorization headers

    try:
        response = requests.delete(url_json, headers=headers, proxies=proxies)
        return response
    except requests.exceptions.ConnectionError:
        return None  # Or return an appropriate response indicating a connection error

def find_post_id_by_url(domain_name, post_url, username, app_password):
    base_url = f"https://{domain_name}/wp-json/wp/v2/posts"
    per_page = 100
    page = 1

    credentials = f"{username}:{app_password}"
    token = base64.b64encode(credentials.encode())
    auth_headers = {'Authorization': 'Basic ' + token.decode('utf-8')}
    headers.update(auth_headers)  # Merge headers with authorization headers

    while True:
        params = {
            'per_page': per_page,
            'page': page
        }
        try:
            response = requests.get(base_url, headers=headers, params=params, proxies=proxies)
            if response.status_code == 400:
                print("Reached end of posts or encountered an error.")
                break
            if response.status_code == 200:
                data = response.json()
                if not data:
                    break
                for post in data:
                    if post['link'] == post_url:
                        return post['id']
                page += 1
            else:
                print(f"Error fetching posts: {response.status_code}")
                break
        except requests.exceptions.ConnectionError:
            return None  # Or return an appropriate response indicating a connection error

    return None  # Return None if post not found or if there was an error



print(test_post_to_wordpress("masterpapers.com.au", "rchauhan", "UrIA IiWL ZkBb phCk AOQO g3LT", "Testing Content"))