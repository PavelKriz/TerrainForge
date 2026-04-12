from flask import Flask, render_template, request, jsonify, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
import map_processing as mp
import uuid
from pathlib import Path

app = Flask(__name__, template_folder='./templates')

# In-memory data store (replace with a database)
data = []

API_ROOT = '/api'
WEB_ROOT = '/'

# GET 
@app.route(f'/', methods=['GET'])
def get_map_selector():
    return render_template('index.html')


# CREATE
@app.route(f'{API_ROOT}/mesh', methods=['POST'])
def create():
    # get variables
    item = request.get_json()
    north = float(item['north'])
    east = float(item['east'])
    south = float(item['south'])
    west = float(item['west'])
    assigned_uuid = str(uuid.uuid4())
    out_image_path = Path("./images").joinpath(secure_filename(f'{assigned_uuid}.png'))
    out_graph_path = Path("./graphs").joinpath(secure_filename(f'{assigned_uuid}.png'))
    out_mesh_path = Path("./mesh").joinpath(secure_filename(f'{assigned_uuid}.stl'))

    # log request
    app.logger.debug(f'Requested roi: ({north}, {east}, {south}, {west})')

    # create mesh and render
    mapdata = mp.MapData(roi=(north, east, south, west))
    # TODO - implement later on with factor in user input
    #mapdata.scale_mesh(factor=2)
    mapdata.render(screenshot_output_path=out_image_path)
    mapdata.render_map_data(screenshot_output_path=out_graph_path)
    mapdata.save_stl(out_mesh_path)
    download_url = url_for('download_page', filename=out_mesh_path.name)
    return jsonify({'download_url': download_url}), 201


@app.route('/download', methods=['GET'])
def download_page():
    filename = request.args.get('filename')
    return render_template('download.html', filename=filename)


@app.route('/stl/<path:filename>', methods=['GET'])
def download_stl(filename):
    return send_from_directory('mesh', filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)