import asyncio
from flask import Flask, render_template, request, jsonify, send_file, session
from services import (process_site, save_data_to_excel, get_all_sitenames, get_url_data_from_db, save_matched_to_excel)
from flask_socketio import SocketIO, emit
import json
from functools import wraps
import openpyxl
import sqlite3
import os
from utils import get_api_keys, openaii

app = Flask(__name__)
# socketio = SocketIO(app, async_mode='threading')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"  # or "None" if necessary
app.config['SESSION_COOKIE_SECURE'] = False

app.secret_key = 'some_secret'

# Set this to True if you want to use images, and False if not.
# USE_IMAGES = True

def get_link_list_from_db(host_url):
    # Establish a connection to the SQLite database
    conn = sqlite3.connect('sites_data.db')
    cursor = conn.cursor()

    # Query to retrieve all the links for a given site
    cursor.execute('''
    SELECT url 
    FROM links
    INNER JOIN sites ON links.site_id = sites.site_id
    WHERE sitename = ?
    ''', (host_url,))

    links = [row[0] for row in cursor.fetchall()]
    conn.close()

    return links


from flask import redirect, url_for, flash


@app.route('/save_api_config', methods=['POST'])
def save_api_config():
    openai_api = request.form.get('openaiapi')
    pexels_api = request.form.get('pexelsapi')

    con = sqlite3.connect('api_config.db')
    cur = con.cursor()

    # Check if the table already contains data
    cur.execute("SELECT COUNT(*) FROM api_keys")
    count = cur.fetchone()[0]

    if count == 0:
        # Insert new APIs
        cur.execute("INSERT INTO api_keys (openai_api, pexels_api) VALUES (?, ?)", (openai_api, pexels_api))
    else:
        # Update existing APIs depending on which fields are filled
        if openai_api and pexels_api:
            cur.execute("UPDATE api_keys SET openai_api = ?, pexels_api = ? WHERE id = 1", (openai_api, pexels_api))
        elif openai_api:
            cur.execute("UPDATE api_keys SET openai_api = ? WHERE id = 1", (openai_api,))
        elif pexels_api:
            cur.execute("UPDATE api_keys SET pexels_api = ? WHERE id = 1", (pexels_api,))

    con.commit()
    con.close()

    flash("API configuration updated successfully!", "success")
    return redirect(url_for('config_manager'))



@app.route('/download_excel')
def download_excel():
    # Specify the file path where the Excel file is saved
    excel_file_path = 'data.xlsx'  # Adjust the path as needed

    # Send the file as a response with appropriate headers
    try:
        return send_file(excel_file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/matched_excel')
def matched_download_excel():
    # Specify the file path where the Excel file is saved
    matched_excel_file_path = 'matched_data.xlsx'  # Adjust the path as needed

    # Send the file as a response with appropriate headers
    try:
        return send_file(matched_excel_file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/uploaded_excel')
def uploaded_download_excel():
    # Specify the file path where the Excel file is saved
    uploaded_excel_file_path = 'uploads/uploaded_excel.xlsx'  # Adjust the path as needed

    # Send the file as a response with appropriate headers
    try:
        return send_file(uploaded_excel_file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/socket_io.js')
def serve_socketio_js():
    return app.send_static_file('socket_io.js')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Dummy logic: replace with real authentication logic
        username = request.form['username']
        password = request.form['password']
        print(f"Received username: {username}, password: {password}")

        if username == "admin" and password == "p@ssword123":  # Dummy check, replace with real logic
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Incorrect credentials.')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)  # Clear the logged_in flag from the session.
    flash('You were successfully logged out.')
    return redirect(url_for('login'))  # Redirect to login page or another page of your choice.


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/config', methods=['GET', 'POST'])
@login_required
def config_manager():
    if request.method == 'POST':
        openai_api = request.form.get('openaiapi').strip()
        pexels_api = request.form.get('pexelsapi').strip()

        con = sqlite3.connect('api_config.db')
        cur = con.cursor()

        # Check if the table already contains data
        cur.execute("SELECT COUNT(*) FROM api_keys")
        count = cur.fetchone()[0]

        if count == 0:
            # Insert new APIs
            cur.execute("INSERT INTO api_keys (openai_api, pexels_api) VALUES (?, ?)", (openai_api, pexels_api))
        else:
            # Update existing APIs depending on which fields are filled
            if openai_api and pexels_api:
                cur.execute("UPDATE api_keys SET openai_api = ?, pexels_api = ? WHERE id = 1", (openai_api, pexels_api))
            elif openai_api:
                cur.execute("UPDATE api_keys SET openai_api = ? WHERE id = 1", (openai_api,))
            elif pexels_api:
                cur.execute("UPDATE api_keys SET pexels_api = ? WHERE id = 1", (pexels_api,))

        con.commit()
        con.close()

        flash("API configuration updated successfully!", "success")

    # Fetch the keys to display
    api_keys = get_api_keys() or {"openai_api": "", "pexels_api": ""}
    return render_template('configuration.html', openai_api=api_keys["openai_api"], pexels_api=api_keys["pexels_api"])



@app.route('/site-manager')
@login_required
def site_manager():
    conn = sqlite3.connect('sites_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sites')
    sites = cursor.fetchall()

    sites_data = []
    print(len(sites))
    for site in sites:
        site_id, sitename, username, app_password = site
        cursor.execute('SELECT url FROM links WHERE site_id = ?', (site_id,))
        links = cursor.fetchall()
        sites_data.append({
            'site_id': site_id,
            'sitename': sitename,
            'username': username,
            'app_password': app_password,
            'links': [link[0] for link in links]
        })

    return render_template('site_manager.html', sites=sites_data)


async def my_async_function():
    await asyncio.sleep(1)
    print("Function executed after 1 second")


def update_excel_with_live_link(file_path, row_index, live_url):
    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active

    # Assuming you want to write to column 'H'
    sheet[f'H{row_index}'] = live_url

    wb.save(file_path)

@app.route('/stop_processing', methods=['POST'])
def stop_processing():
    global should_continue_processing
    should_continue_processing = False
    return jsonify({"message": "Processing will be stopped."}), 200


@app.route('/start_emit', methods=['POST'])
def start_emit():
    global should_continue_processing
    global USE_IMAGES
    print(openaii)
    should_continue_processing = True

    # Get the Excel file
    excel_file = request.files['excel_file']
    if not excel_file:
        return jsonify({"error": "No file uploaded."}), 400

    # Set USE_IMAGES based on checkbox value
    USE_IMAGES = 'use_images' in request.form

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], "uploaded_excel.xlsx")
    excel_file.save(file_path)

    # Load the workbook and select the active sheet
    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active

    # Create an empty list to accumulate the data
    data_list = []
    sitenames = get_all_sitenames()
    num_sites = len(sitenames)

    total_rows = len(list(sheet.iter_rows(values_only=True)))
    row_index = 0

    last_used_site_index = -1  # Start with -1 so that for the first row, it starts with 0.

    while row_index < total_rows and should_continue_processing:
        row = list(sheet.iter_rows(values_only=True))[row_index]
        print(row)

        if row_index == 0:
            row_index += 1
            continue
        if row[1] is None or row[2] is None:
            row_index += 1
            continue

        asyncio.run(my_async_function())
        anchor, linking_url, embed_code, map_embed_title, nap, topic, live_link = row[1:8]

        if row[7] != None and row[7] != "Failed To Post":
            print("skipping the site")
            row_index += 1
            continue


        link_posted = False
        failed_post_count = 0  # Counter for failed posts.
        start_site_index = (last_used_site_index + 1) % num_sites  # Start from the next site.

        for offset in range(num_sites):
            site_index = (start_site_index + offset) % num_sites  # Wrap around using modulo.
            host_url = sitenames[site_index]
            link_list = get_link_list_from_db(host_url)

            # Inside the success condition where you've successfully posted the link:
            last_used_site_index = site_index  # Update the last used site index.

            if linking_url in link_list:
                print(f"Matched{link_list} in host:{host_url}")
                print("Matched Link inside")
                save_matched_to_excel(site_index, host_url, linking_url)
                continue

            user_password_data = get_url_data_from_db(host_url)
            site_json = "https://" + host_url + "/wp-json/wp/v2"

            if user_password_data:
                user = user_password_data.get('user')
                password = user_password_data.get('password')

                for _ in range(5):
                    asyncio.run(my_async_function())

                live_url = process_site(site_json, host_url, user, password, topic, anchor, linking_url, embed_code,
                                        map_embed_title, nap, USE_IMAGES)

                if live_url == "Failed To Post":
                    failed_post_count += 1
                    if failed_post_count < 3:
                        continue
                    else:
                        break

                update_excel_with_live_link(file_path, row_index + 1, live_url)

                data = {
                    'id': row_index,
                    'anchor': anchor,
                    'linking_url': linking_url,
                    'nap': nap,
                    'topic': topic,
                    'live_url': live_url,
                    "Host_site": host_url,
                }
                data_list.append(data)
                socketio.emit('update', {'data': json.dumps(data_list)})
                save_data_to_excel(data_list)

                link_posted = True
                break

        if not link_posted:
            print("All Sites have this link")
            pass

        row_index += 1

    if not should_continue_processing:
        print("Process stopped")
        flash("Process stopped")
        socketio.emit('update', {"message": "Process stopped"})
        return jsonify({"message": "Processing was halted by the user."}), 200

    flash("Processed successfully!")
    socketio.emit('update', {"message": "Processing complete."})
    return jsonify({"message": "Processing complete."}), 200



if __name__ == '__main__':
    socketio.run(app, debug=True)
