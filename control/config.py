from dotenv import load_dotenv
import os


# Load .env file
load_dotenv()
ENV_URL_SERVICE_RESOURCES = os.getenv('ENV_URL_SERVICE_RESOURCES')
ENV_DEBUG = os.getenv('ENV_DEBUG')