# TrussGPT

A web-based , vibecoded truss structure analysis application powered by AI. TrussGPT combines Finite Element Method (FEM) analysis with an AI-powered chat interface for structural engineering calculations and insights.

## Features

- **Truss Structure Analysis**: Perform 2D truss analysis using the Finite Element Method
- **Interactive Web Interface**: Add nodes, elements, and loads through a user-friendly UI
- **Real-time Calculations**: Compute displacements, forces, and stresses
- **Visualization**: Generate deformation plots with axial force distribution
- **AI Chat Integration**: Ask questions about your truss analysis results in English or Persian
- **Safety Analysis**: Automatic checking for yield and ultimate stress failure

## Tech Stack

- **Backend**: Python 3.13+ with Flask
- **Frontend**: HTML, CSS, JavaScript
- **Numerical Computing**: NumPy
- **Visualization**: Matplotlib
- **AI Integration**: OpenAI API

## Installation

### Prerequisites

- Python 3.13 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/tahaSadeghi2308/TrussGPT.git
   cd TrussGPT
   ```

2. Install dependencies using uv:
   ```bash
   uv sync
   ```

3. Create a `.env` file in the app folder with the following variables:
   ```env
   SECRET_KEY=your-secret-key
   BASE_URL=https://api.openai.com/v1  # or your custom OpenAI-compatible API URL
   USERNAME=your-login-username
   PASSWORD=your-login-password
   SK=your-flask-secret-key
   ```

## Usage

### Running the Application

```bash
uv run python -m app.app
```

The application will be available at `http://localhost:5000`

### Workflow

1. **Login**: Access the application using your configured credentials
2. **Define Nodes**: Add nodes with coordinates (x, y) and boundary conditions (ux, uy restraints)
3. **Define Elements**: Connect nodes with elements, specifying material and cross-sectional area
4. **Apply Loads**: Add forces (fx, fy) to nodes
5. **Calculate**: Run the truss analysis
6. **Visualize**: View the deformation plot with force distribution
7. **Chat with AI**: Ask questions about your analysis results

## Project Structure

```
TrussGPT/
├── app/
│   ├── __init__.py
│   ├── app.py              # Main Flask application
│   ├── config.py           # Configuration management
│   ├── api/
│   │   ├── chat_api.py     # AI chat endpoints
│   │   ├── login_api.py    # Authentication endpoints
│   │   └── turss_info_api.py  # Truss data CRUD operations
│   ├── logic/
│   │   ├── models.py       # Node, Element, Material classes
│   │   ├── truss_calculator.py  # FEM calculation functions
│   │   ├── truss_data.py   # Global data storage
│   │   └── calculations.py # Additional calculations
│   ├── static/
│   │   ├── css/            # Stylesheets
│   │   └── js/             # JavaScript files
│   ├── templates/
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── truss_info.html
│   │   └── chat.html
│   └── utils/
│       └── reset.py        # Utility functions
├── pyproject.toml
├── LICENSE
└── README.md
```

## API Endpoints

### Truss Data
- `GET /api/truss-data` - Get all nodes, elements, and materials
- `POST /api/nodes` - Add a new node
- `POST /api/elements` - Add a new element
- `POST /api/calculate` - Run truss analysis
- `GET /api/truss/image` - Get deformation plot

### Chat
- `POST /api/chat/req` - Send message to AI assistant

### Authentication
- `POST /api/login` - User login
- `POST /api/logout` - User logout

## FEM Analysis

The truss analysis uses the Direct Stiffness Method:

1. **Global Stiffness Matrix Assembly**: Assembles element stiffness matrices into global matrix
2. **Boundary Conditions**: Applies restraints (fixed supports)
3. **Solve Displacements**: Solves `K * u = F` for nodal displacements
4. **Compute Forces**: Calculates axial forces in each element
5. **Check Failure**: Compares stresses against yield and ultimate strength

## Supported Materials

Materials can be defined with:
- Young's Modulus (E)
- Yield Strength (Sy)
- Ultimate Strength (Su)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

## Acknowledgments

- Finite Element Method for structural analysis
- OpenAI for AI integration capabilities
- Flask framework for web application structure
