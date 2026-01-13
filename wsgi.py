#from dotenv import load_dotenv
#import os

#load_dotenv(dotenv_path="/home/magsud/work/Yonca/.env")

#load_dotenv()  # Load environment variables from .env

from yonca import create_app

app = create_app('production')

if __name__ == "__main__":
    app.run()