from flask import Flask, render_template, request, jsonify, url_for, send_from_directory
from werkzeug.utils import secure_filename
import map_processing as mp
import uuid
from pathlib import Path


app = Flask(__name__, template_folder='./templates')


API_ROOT = '/api'
WEB_ROOT = '/'


MAX_ROI_SIZE_METERS = 50000  # Maximum allowed size for the region of interest (in meters)


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

    # log request
    app.logger.debug(f'Requested roi: ({north}, {east}, {south}, {west})')

    # check the size of input roi
    lat_width = mp.MapData.lat_deg_to_m(abs(north - south))
    long_width = mp.MapData.long_deg_to_m_at_lat((north + south) / 2, abs(east - west))
    if lat_width > MAX_ROI_SIZE_METERS or long_width > MAX_ROI_SIZE_METERS:
        return jsonify({'error': 'ROI size exceeds the maximum allowed size.'}), 400

    # create path variables
    assigned_uuid = str(uuid.uuid4())
    out_image_path = Path("./images").joinpath(secure_filename(f'{assigned_uuid}.png'))
    out_graph_path = Path("./graphs").joinpath(secure_filename(f'{assigned_uuid}.png'))
    out_mesh_path = Path("./mesh").joinpath(secure_filename(f'{assigned_uuid}.stl'))

    

    # create mesh and render
    mapdata = mp.MapData(roi=(north, east, south, west))
    # TODO - implement later on with factor in user input
    # mapdata.scale_mesh(factor=2)
    mapdata.render(screenshot_output_path=out_image_path)
    mapdata.render_map_data(screenshot_output_path=out_graph_path)
    mapdata.save_stl(out_mesh_path)
    download_url = url_for('download_page', filename=out_mesh_path.name)
    return jsonify({'download_url': download_url}), 201


@app.route('/download', methods=['GET'])
def download_page():
    filename = secure_filename(request.args.get('filename'))
    # Verify the file exists in the mesh directory
    filepath = Path("./mesh").joinpath(filename)
    if not filepath.exists() or not filepath.is_file():
        return jsonify({'error': 'File not found.'}), 404
    return render_template('download.html', filename=filename)


@app.route('/mesh/<path:filename>', methods=['GET'])
def download_stl(filename):
    return send_from_directory('mesh', secure_filename(filename), as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)