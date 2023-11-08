import requests
import json
from utils import openAI_output, Pexels_API_KEY
from PIL import Image
import base64
import openpyxl
import re
import os
from config import Pexels_API_ENDPOINT
from random import randrange
import random
from urllib.parse import urlparse


# Image Operations
def process_image(keyword, USE_IMAGES):
    if not USE_IMAGES:
        return None
    print("Processing Image")

    image_headers = {
        "Authorization": Pexels_API_KEY
    }

    params = {
        "query": keyword
    }

    response = requests.get(Pexels_API_ENDPOINT, headers=image_headers, params=params)


    if response.status_code == 200:
        data = response.json()
        try:
            r = data['photos'][randrange(0, 6)]['src']['medium']
            print("Pexel Image Received")
        except:
            r = data['photos'][randrange(0, 3)]['src']['medium']
            print("Pexel Image Received at except")

        img_data = requests.get(r).content


        # Check and create folder structure if not exists
        folder_path = 'images'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Save the image
        image_path = os.path.join(folder_path, 'temp-image.jpg')
        with open(image_path, 'wb') as handler:
            handler.write(img_data)

        im = Image.open(image_path)

        im1 = im.resize((570, 330))

        slugified_keyword = keyword.replace(' ', '-').lower()
        saved_path = os.path.join(folder_path, f'{slugified_keyword}-image.jpg')
        try:
            im1.save(saved_path)
        except IOError as e:
            print(f"Error saving image: {e}")

        return saved_path

def delete_all_images_in_folder(folder_path='images'):
    # List all files in the directory
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Check if it's a file
        if os.path.isfile(file_path):
            os.remove(file_path)

def upload_image_data(target_url, headers, image_path):
    if image_path is None:
        # handle the case where no image is provided, perhaps return a default value or error
        return None
    with open(image_path, 'rb') as img_file:
        try:
            media = {'file': img_file}
            response = requests.post(target_url + '/media', headers=headers, files=media)
            img_file.close()
            delete_all_images_in_folder()
            return json.loads(response.content)
        except:
            print("image posting error")
            return None


def construct_image_wp(image_data, query):
    if image_data != None:
        try:
            image_title = query.replace('-', ' ').split('.')[0]
            post_id = str(image_data['id'])
            source = image_data['guid']['rendered']

            image1 = '<!-- wp:image {"align":"center","id":' + post_id + ',"sizeSlug":"full","linkDestination":"none"} -->'
            image2 = '<div class="wp-block-image"><figure class="aligncenter size-full"><img src="' + source + '" alt="' + image_title + '" title="' + image_title + '" class="wp-image-' + post_id + '"/></figure></div>'
            image3 = '<!-- /wp:image -->'
            image_wp = image1 + image2 + image3
        except:
            image_wp = ""
            post_id = ""
    else:
        image_wp = ""
        post_id = ""

    return image_wp, post_id


# WordPress Posting
def create_post_content(anchor, topic, linking_url, image_data, embed_code, map_embed_title, nap, USE_IMAGES, NO_BODY_IMAGE):

    image_wp, post_id = construct_image_wp(image_data, anchor) if USE_IMAGES else ("", None)

    intro_body = openAI_output(
        f"Create an introduction for the article on {topic}. Give use <p></p> in each para. Not exceed 2 paragraph")

    # Define the HTML tags and content
    h2_heading = "<h2></h2>"
    link_tag = f"<a href='{linking_url}' rel='dofollow'>{anchor}</a>"

    paragraph_template = f"<p></p> Please insert the provided HTML tag, which is {link_tag}, inside ONLY ANY ONE of the paragraphs. The anchor link should be used ONLY ONCE and it must be within a paragraph, not outside. Do not alter the anchor tag or the link."

    # Create 1-2 paragraphs with a maximum of 1-2 H2 headings (No introduction)
    second_body = openAI_output(
        f"Create 1-2 paragraphs with a maximum of 1-2 H2 headings (No introduction). Use the {h2_heading} tags for the heading. Also, ensure to follow the {paragraph_template} instructions for the paragraph."
    )
    try:
        second_body_formated = ((second_body).replace("nofollow", "dofollow")).replace("noopener", "dofollow")
    except:
        second_body_formated = second_body



    def replace_link(match):
        original_tag = match.group(0)
        new_url = linking_url
        new_anchor = anchor
        new_tag = re.sub(r"href=[\"'][^\"']+[\"']", f'href="{new_url}"', original_tag)
        new_tag = re.sub(r'>([^<]+)<', f'>{new_anchor}<', new_tag)
        return new_tag


    # Removing <p></p> tags if they wrap <a> tags
    second_body_formated = re.sub(r'<p>(<a [^>]+>.*?</a>)</p>', r'\1', second_body_formated)

    # Replacing links
    linking_url = linking_url
    anchor = anchor
    second_body_formated_final = re.sub(r"<a href=[\"']([^\"']+)[\"'][^>]+rel=[\"']dofollow[\"']>[^<]+<\/a>",
                                        replace_link, second_body_formated)




    first_part = intro_body + second_body_formated_final
    final_part = openAI_output(
            f"Write the final part with one paragraphs on the topic {topic}. The previous part is {first_part}. Don't "
            f"put any links.")

    print("Middle of Creating Content")


    if embed_code != None:
        embed_code = embed_code
    else:
        embed_code = ""

    if map_embed_title != None:
        map_embed_title = map_embed_title
    else:
        map_embed_title = ""
    if nap != None:
        nap = nap
    else:
        nap = ""
    try:
        if USE_IMAGES:
            if not NO_BODY_IMAGE:
                content = intro_body +"<br>" + image_wp + second_body + map_embed_title + embed_code + "<br>" + "<p>" + nap + "</p>" + final_part
            else:
                content = intro_body +"<br>" + second_body + map_embed_title + embed_code + "<br>" + "<p>" + nap + "</p>" + final_part
        else:
            content = first_part + "<br>" + map_embed_title + embed_code + "<br>" + "<p>" + nap + "</p>" + final_part
    except:
        content = ""
    return content


def post_article(target_url, headers, query, content, post_id, USE_IMAGES):
    title = openAI_output(f"Write an SEO optimized title for a simple article the TOPIC: {query}. Title should not "
                          f"excess 50-55 characters")

    def custom_title(s):
        try:
            s = s.replace("“", "").replace("”", "").replace("\"", "")
            s = s.title()
            s = s.replace("’S", "’s")
        except:
            s = s
        return s


    formatted_title = custom_title(title)

    print("title:", formatted_title)

    post_data = {
        'title': formatted_title,
        'slug': title,
        'status': "publish",
        'categories': 1,
        'content': content,
    }

    if USE_IMAGES:
        post_data = {
            'title': formatted_title,
            'slug': title,
            'status': "publish",
            'content': content,
            'categories': 1,
            'featured_media': post_id
        }

    try:
        print("Start Posting")
        response = requests.post(target_url + '/posts', headers=headers, json=post_data)
        print(response.status_code)
        # Decode the bytes content to a string
        response_content_str = response.content.decode('utf-8')
        # Parse the JSON data
        datas = json.loads(response_content_str)
        slug_url = datas["link"]
        live_link = slug_url
        print(live_link)
    except:
        slug_url = "Failed To Post"
        live_link = slug_url
        print(live_link)

    return live_link

# Database Operation
import sqlite3

DATABASE_NAME = "sites_data.db"


# Utility function to simplify connection creation
def connect_db():
    return sqlite3.connect(DATABASE_NAME)


def get_url_data_from_db(t_url):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, app_password FROM sites WHERE sitename=?", (t_url,))
    data = cursor.fetchone()
    conn.close()
    if data:
        return {'user': data[0], 'password': data[1]}
    else:
        return None


def get_all_sitenames():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT sitename FROM sites")
    sitenames = [row[0] for row in cursor.fetchall()]

    conn.close()

    random.shuffle(sitenames)

    return sitenames

def get_site_id_from_sitename(sitename):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT site_id FROM sites WHERE sitename=?", (sitename,))
    site_id = cursor.fetchone()
    conn.close()
    return site_id[0] if site_id else None


def store_posted_url(sitename, url):
    site_id = get_site_id_from_sitename(sitename)
    if site_id:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO links (site_id, url) VALUES (?, ?)", (site_id, url))
        conn.commit()
        conn.close()
    else:
        print(f"Error: No site_id found for sitename {sitename}")


def delete_site_and_links(sitename):
    site_id = get_site_id_from_sitename(sitename)
    if site_id:
        conn = connect_db()
        cursor = conn.cursor()

        # Start a transaction
        cursor.execute("BEGIN TRANSACTION")

        # First, delete associated links
        cursor.execute("DELETE FROM links WHERE site_id=?", (site_id,))

        # Then, delete the site
        cursor.execute("DELETE FROM sites WHERE site_id=?", (site_id,))

        # Commit the transaction
        conn.commit()
        conn.close()
    else:
        print(f"Error: No site_id found for sitename {sitename}")


# Matching Exact Root Domain
def extract_domain(url):
    try:
        # Use urlparse to break the URL into components
        parsed_url = urlparse(url)

        # Extract the 'netloc' component for the domain
        domain = parsed_url.netloc

        return domain
    except Exception as e:
        print(f"An error occurred: {e}")
        return None



# Excel Operation
def save_matched_to_excel(site_index, sitename, linking_url):
    file_name = 'matched_data.xlsx'

    # Create a new Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    headers = ['Site Index', 'Sitename', 'Matched Linking URL']
    ws.append(headers)

    # Append the matched data
    row_data = [site_index, sitename, linking_url]
    ws.append(row_data)

    # Save the Excel file
    wb.save(file_name)



def process_site(site_json, user, password, topic, anchor, client_link, embed_code, map_embed_title, nap, USE_IMAGES, NO_BODY_IMAGE):
    credentials = user + ':' + password
    token = base64.b64encode(credentials.encode())
    headers = {'Authorization': 'Basic ' + token.decode('utf-8')}
    print("Start Process Site")
    # download_image(topic)
    image_path = process_image(topic, USE_IMAGES)
    print(image_path)
    if USE_IMAGES:
        image_data = upload_image_data(site_json, headers, image_path)
        image_wp, post_id = construct_image_wp(image_data, topic)
        print("Image Posted")
    else:
        image_data = None  # or some default value
        post_id = ""
    print("Start Content Creation")
    try:
        final_content = create_post_content(anchor, topic, client_link, image_data, embed_code, map_embed_title, nap, USE_IMAGES, NO_BODY_IMAGE)
    except:
        final_content = ""
    print("before post url")
    post_url = post_article(site_json, headers, topic, final_content, post_id, USE_IMAGES)

    return post_url

