# TerraMeshify

TerraMeshify is a web-based application that allows users to select regions on an interactive map and generate 3D printable STL meshes from elevation data. The application fetches topographic data, processes it into a 3D mesh, and provides downloadable STL files for 3D printing. You can see the service deployed at: https://terrameshify.pavelkriz.com/

> **NOTE 🗒️:** this a valuable project for anyone who would want to study the principle without complex source code. Who would like to export files for 3d print i recommend this web: https://map2model.com/ tool.

## Features

- Interactive map interface using Leaflet for region selection
- Real-time elevation data fetching from OpenTopoMap
- 3D mesh generation from topographic data
- STL file export for 3D printing
- Screenshot generation of the 3D model and map data
- RESTful API for programmatic access
- Docker containerization for easy deployment

## Installation

### Prerequisites

- Python 3.12 or higher
- Docker (optional, for containerized deployment)

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd terrameshify
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create configuration `config.yaml` in the project directory:
   ```yaml
   topo_api_key_path: PATH_TO_OPENTOPOGRAPHY_API_KEY_TXT
   ```

4. Place your opentopography key in a plain text file

5. Run the application and open in browser at `http://localhost:5000`:
   ```bash
   python api.py
   ```

### Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t terrameshify .
   ```

2. Run the container:
   ```bash
   docker run --mount type=bind,source=$(pwd)/prod_config.yaml,target=/terrameshify/config.yaml --mount type=bind,source=PATH_TO_API_KEY.txt,target=/PATH_TO_API_KEY.txt -p 8080:8080 terrameshify:latest 
   ```

3. Access the application at `http://localhost:8000`

## Usage

### Web Interface

1. Open the application in your web browser
2. Use the interactive map to draw a rectangle around the area you want to convert to a 3D mesh
3. Click the "Generate Mesh" button
4. Wait for processing to complete
5. Download the STL file from the provided link

### API Usage

The application provides a REST API for programmatic access:

#### Create Mesh

**POST** `/api/mesh`

Request body:
```json
{
  "north": 40.0,
  "east": -74.0,
  "south": 39.0,
  "west": -75.0
}
```

Response:
```json
{
  "download_url": "/download?filename=generated-uuid.stl"
}
```

#### Download STL

**GET** `/stl/{filename}`

Returns the STL file as an attachment.

## Project Structure

```
terrameshify/
├── api.py                 # Main Flask application
├── wsgi.py               # WSGI entry point for production
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── templates/           # HTML templates
│   ├── index.html       # Main map interface
│   └── download.html    # Download page
├── map_processing/      # Core map processing logic
│   ├── __init__.py
│   ├── map_data.py      # MapData class for elevation processing
│   └── map_data_provider.py  # Data provider for topographic data
├── images/              # Generated screenshots
├── graphs/              # Generated graph images
├── mesh/                # Generated STL files
└── tests/               # Test files
```

## Dependencies

Installed in requirements files `requirements.txt`

## Development

### Code Style

This project follows PEP 8 guidelines. Use tools like `black` and `flake8` for code formatting and linting.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

[Specify your license here]

## Acknowledgments

- OpenTopoMap for elevation data
- Leaflet for the interactive map component
- PyVista for 3D mesh processing