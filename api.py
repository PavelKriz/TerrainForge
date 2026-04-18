from flask import Flask, render_template, request, jsonify, url_for, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
import map_processing as mp
import uuid
from pathlib import Path
from math import isfinite
import time
import yaml


app = Flask(__name__, template_folder='./templates')

with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)
api_key_path = config["topo_api_key_path"]

map_data_provider = mp.BmiOpenTopoMapDataProvider(api_key_path)

API_ROOT = '/api'
WEB_ROOT = '/'


MAX_ROI_SIZE_METERS = 50000  # Maximum allowed size for the region of interest (in meters)
# limit the size of incoming JSON to prevent abuse
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024  # 1 KB is plenty for coordinate JSON

REQUIRED_COORD_FIELDS = ('north', 'east', 'south', 'west')
MESH_RATE_LIMIT = '5 per minute'
GENERAL_RATE_LIMIT ='20 per minute'  # General rate limit for non-mesh endpoints, can be adjusted as needed
RATE_LIMIT_STORAGE_URI = config.get('rate_limit_storage_uri', 'memory://')
ARTIFACT_TTL_SECONDS = 24 * 60 * 60
ARTIFACT_MAX_FILES_PER_DIR = 50
ARTIFACT_DIRECTORIES = (
    Path('./images'),
    Path('./graphs'),
    Path('./mesh'),
)

# Rate limiter setup - a tool to limit the number of requests a client can make to the API in a given time frame to prevent abuse and ensure fair usage.
# For one app, one process setup, the in-memory storage is sufficient and simple to use. For more complex setups (e.g., multiple processes or distributed systems), consider using a shared storage backend like Redis.
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    storage_uri=RATE_LIMIT_STORAGE_URI,
    default_limits=[],
)

# TODO not very robust or speedy cleanup strategy, but should work for a simple prototype. Consider more robust solutions for production.
def cleanup_artifacts() -> None:
    """Remove stale files and enforce per-directory file cap."""
    now = time.time()
    for directory in ARTIFACT_DIRECTORIES:
        if not directory.exists():
            continue

        files = [
            path for path in directory.iterdir()
            if path.is_file() and path.name != '.gitkeep'
        ]
        for path in files:
            try:
                if (now - path.stat().st_mtime) > ARTIFACT_TTL_SECONDS:
                    path.unlink(missing_ok=True)
            except OSError:
                app.logger.warning('Failed to delete stale artifact: %s', path)

        # Re-scan after stale cleanup and keep only the newest capped set.
        files = [
            path for path in directory.iterdir()
            if path.is_file() and path.name != '.gitkeep'
        ]
        if len(files) <= ARTIFACT_MAX_FILES_PER_DIR:
            continue

        files_sorted = sorted(files, key=lambda file_path: file_path.stat().st_mtime)
        overflow_count = len(files_sorted) - ARTIFACT_MAX_FILES_PER_DIR
        for path in files_sorted[:overflow_count]:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                app.logger.warning('Failed to delete overflow artifact: %s', path)


def parse_mesh_request():
    """Parse and validate mesh request payload."""
    item = request.get_json(silent=True)
    if not isinstance(item, dict):
        return None, (jsonify({'error': 'Invalid JSON payload.'}), 400)

    missing_fields = [field for field in REQUIRED_COORD_FIELDS if field not in item]
    if missing_fields:
        return None, (jsonify({'error': f"Missing required fields: {', '.join(missing_fields)}"}), 400)

    coords = {}
    try:
        for field in REQUIRED_COORD_FIELDS:
            value = float(item[field])
            if not isfinite(value):
                raise ValueError
            coords[field] = value
    except (TypeError, ValueError):
        return None, (jsonify({'error': 'Coordinates must be finite numbers.'}), 400)

    return coords, None


# Error handler for rate limit exceeded
@app.errorhandler(429)
def handle_rate_limit(_error):
    return jsonify({'error': 'Rate limit exceeded. Please retry later.'}), 429


# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200


# GET 
@app.route(f'/', methods=['GET'])
@limiter.limit(GENERAL_RATE_LIMIT)
def get_map_selector():
    return render_template('index.html')


# CREATE
@app.route(f'{API_ROOT}/mesh', methods=['POST'])
@limiter.limit(MESH_RATE_LIMIT)
def create():
    coords, error_response = parse_mesh_request()
    if error_response is not None:
        return error_response
    
    # TODO not very robust or speedy cleanup strategy, but should work for a simple prototype. Consider more robust solutions for production.
    cleanup_artifacts()

    north = coords['north']
    east = coords['east']
    south = coords['south']
    west = coords['west']

    # log request
    app.logger.debug(f'Requested roi: ({north}, {east}, {south}, {west})')

    # check the size of input roi
    lat_width = mp.MapData.lat_deg_to_m(abs(north - south))
    long_width = mp.MapData.long_deg_to_m_at_lat((north + south) / 2, abs(east - west))
    if lat_width > MAX_ROI_SIZE_METERS or long_width > MAX_ROI_SIZE_METERS:
        return jsonify({'error': 'ROI size exceeds the maximum allowed size.'}), 400

    # check if coordinates are valid
    if not (-90 <= south < north <= 90) or not (-180 <= west < east <= 180):
        return jsonify({'error': 'Invalid coordinates.'}), 400

    # create path variables
    assigned_uuid = str(uuid.uuid4())
    out_image_path = Path("./images").joinpath(secure_filename(f'{assigned_uuid}.png'))
    out_graph_path = Path("./graphs").joinpath(secure_filename(f'{assigned_uuid}.png'))
    out_mesh_path = Path("./mesh").joinpath(secure_filename(f'{assigned_uuid}.stl'))

    # create mesh and render
    mapdata = mp.MapData(data_provider=map_data_provider,\
                         roi=(north, east, south, west))
    # TODO - implement later on with factor in user input
    # mapdata.scale_mesh(factor=2)
    mapdata.render(screenshot_output_path=out_image_path)
    mapdata.render_map_data(screenshot_output_path=out_graph_path)
    mapdata.save_stl(out_mesh_path)
    download_url = url_for('download_page', artifact_id=assigned_uuid)
    return jsonify({'download_url': download_url}), 201


@app.route('/download', methods=['GET'])
@limiter.limit(GENERAL_RATE_LIMIT)
def download_page():
    artifact_id = secure_filename(request.args.get('artifact_id', ''))
    if not artifact_id:
        return jsonify({'error': 'Missing artifact_id.'}), 400

    mesh_filename = secure_filename(f'{artifact_id}.stl')
    # Verify the file exists in the mesh directory
    filepath = Path("./mesh").joinpath(mesh_filename)
    if not filepath.exists() or not filepath.is_file():
        return jsonify({'error': 'File not found.'}), 404
    return render_template('download.html', artifact_id=artifact_id)


@app.route('/images/<string:filename>', methods=['GET'])
@limiter.limit(GENERAL_RATE_LIMIT)
def preview_image(filename):
    return send_from_directory('images', secure_filename(filename))


@app.route('/graphs/<string:filename>', methods=['GET'])
@limiter.limit(GENERAL_RATE_LIMIT)
def graph_image(filename):
    return send_from_directory('graphs', secure_filename(filename))


@app.route('/mesh/<string:filename>', methods=['GET'])
@limiter.limit(GENERAL_RATE_LIMIT)
def download_stl(filename):
    return send_from_directory('mesh', secure_filename(filename), as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)