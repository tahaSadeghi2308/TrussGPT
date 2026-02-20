from app.logic.truss_data import nodes, elements
from pathlib import Path
import os

LOGIC_FOLDER = Path(__file__).parent.parent / "logic"
RESULTS_FILE = LOGIC_FOLDER / "truss_results.json"
IMAGE_FILE = LOGIC_FOLDER / "truss_deformation.png"

def reset_project_data():
    nodes.clear()
    elements.clear()
    if RESULTS_FILE.exists():
        try:
            os.remove(RESULTS_FILE)
        except:
            pass
    if IMAGE_FILE.exists():
        try:
            os.remove(IMAGE_FILE)
        except:
            pass