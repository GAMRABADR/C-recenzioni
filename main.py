import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Importa l'app inizializzata
from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
