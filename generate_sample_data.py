# generate_sample_data.py
import os
from dotenv import load_dotenv
from pexels_api import API
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Listing
import random

load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
if not PEXELS_API_KEY:
    raise ValueError("Please set the PEXELS_API_KEY in your .env file")

pexels = API(PEXELS_API_KEY)

def get_house_images(count: int = 10):
    images = []
    page = 1
    while len(images) < count:
        response = pexels.search("house", page=page, results_per_page=40)
        if response and "photos" in response:
            for photo in response["photos"]:
                images.append({
                    "url": photo["src"]["large"],
                    "width": photo["width"],
                    "height": photo["height"]
                })
            page += 1
        else:
            break
    return images[:count]

def generate_sample_listings(db: Session, count: int = 10):
    images = get_house_images(count)
    
    for i, image in enumerate(images, 1):
        listing = Listing(
            title=f"Beautiful House {i}",
            description=f"This is a lovely house with all modern amenities. Perfect for a family of {random.randint(2, 6)}.",
            price=random.randint(200000, 1000000),
            image_url=image["url"],
            image_width=image["width"],
            image_height=image["height"]
        )
        db.add(listing)
    
    db.commit()
    print(f"{count} sample listings have been added to the database.")

if __name__ == "__main__":
    db = SessionLocal()
    generate_sample_listings(db)
    db.close()
