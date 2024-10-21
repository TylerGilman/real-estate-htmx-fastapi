# real-estate-htmx-fastapi
Project for CS3200 using fastapi and htmx. Real estate website where admin users can preform CRUD operations on a database of houses.

# Prerender on hover for fast render.


## Image to Image Search
https://medium.com/@tenyks_blogger/how-to-build-an-image-to-image-search-tool-using-clip-pinecone-b7b70c44faac#:~:text=A%20vector%20similarity%20search%20is,most%20visually%20similar%20search%20results.

# Startup

## Make and activate python virtual environment
pip install virtualenv \
python3 -m venv .venv \
source .venv/bin/activate

## Install dependencies
pip install -r requirements.txt

## Run Development Environment 
uvicorn main:app --reload
