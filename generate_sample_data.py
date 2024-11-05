import os
from dotenv import load_dotenv
from pexels_api import API
from sqlalchemy.orm import Session
from database import SessionLocal
from models import (
    Property,
    PropertyType,
    ResidentialProperty,
    CommercialProperty,
    Brokerage,
    Agent,
    Client,
    AgentListing,
    AgentRole,
    ClientType,
)
import random
from faker import Faker
from datetime import datetime
import sys

# Initialize Faker
fake = Faker()

# Load environment variables
load_dotenv()


def get_house_images(count: int = 50):
    """Get images from Pexels API or return placeholder images if API fails"""
    try:
        PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
        if not PEXELS_API_KEY:
            raise ValueError("No Pexels API key found")

        pexels = API(PEXELS_API_KEY)
        images = []
        page = 1

        response = pexels.search("house", page=page, results_per_page=count)
        if response and "photos" in response:
            for photo in response["photos"]:
                images.append(
                    {
                        "url": photo["src"]["large"],
                        "width": photo["width"],
                        "height": photo["height"],
                    }
                )
            return images[:count]
        else:
            raise Exception("No photos found in Pexels response")

    except Exception as e:
        print(f"Failed to get images from Pexels: {e}")
        print("Using placeholder images instead")
        # Return placeholder images
        return [
            {
                "url": f"https://picsum.photos/800/600?random={i}",
                "width": 800,
                "height": 600,
            }
            for i in range(count)
        ]


def generate_sample_data(db: Session, property_count: int = 50):
    try:
        print("Starting sample data generation...")

        # Get images
        print("Getting images...")
        images = get_house_images(property_count)
        print(f"Got {len(images)} images")

        # Create a brokerage
        print("Creating brokerage...")
        brokerage = Brokerage(
            broker_name="Cherokee Street Real Estate",
            broker_address="123 Cherokee Street",
            broker_phone="(555) 123-4567",
        )
        db.add(brokerage)
        db.commit()
        print(f"Created brokerage: {brokerage.broker_id}")

        # Create agents
        print("Creating agents...")
        agents = []
        for i in range(5):
            agent = Agent(
                nrds=f"NRDS{100000 + i}",
                ssn=fake.unique.ssn(),
                agent_name=fake.name(),
                agent_phone=fake.phone_number(),
                broker_id=brokerage.broker_id,
            )
            db.add(agent)
            agents.append(agent)
        db.commit()
        print(f"Created {len(agents)} agents")

        # Create clients
        print("Creating clients...")
        clients = []
        for i in range(property_count):
            client = Client(
                ssn=fake.unique.ssn(),
                client_name=fake.name(),
                mailing_address=fake.address(),
                client_phone=fake.phone_number(),
                client_type=random.choice(list(ClientType)),
                intent=random.choice(["purchase", "lease"]),
            )
            db.add(client)
            clients.append(client)
        db.commit()
        print(f"Created {len(clients)} clients")

        # Create properties
        print("Creating properties...")
        properties_created = 0
        for i, image in enumerate(images):
            try:
                # Determine if residential or commercial
                is_residential = random.random() < 0.7  # 70% residential

                # Create base property
                tax_id = f"TAX{100000 + i}"
                address = fake.unique.address()

                property = Property(
                    tax_id=tax_id,
                    property_address=address,
                    status=random.choice(["For Sale", "For Lease"]),
                    price=random.randint(200000, 1000000),
                    image_url=image["url"],
                    image_width=image["width"],
                    image_height=image["height"],
                    property_type=(
                        PropertyType.RESIDENTIAL
                        if is_residential
                        else PropertyType.COMMERCIAL
                    ),
                )
                db.add(property)
                db.flush()

                # Create property details
                if is_residential:
                    residential = ResidentialProperty(
                        tax_id=tax_id,
                        property_address=address,
                        bedrooms=random.randint(2, 6),
                        bathrooms=random.choice([1, 1.5, 2, 2.5, 3, 3.5, 4]),
                        r_type=random.choice(
                            ["Single Family", "Condo", "Townhouse", "Apartment"]
                        ),
                    )
                    db.add(residential)
                else:
                    commercial = CommercialProperty(
                        tax_id=tax_id,
                        property_address=address,
                        sqft=random.uniform(1000, 50000),
                        industry=random.choice(
                            ["Retail", "Office", "Industrial", "Mixed Use"]
                        ),
                        c_type=random.choice(
                            [
                                "Office Building",
                                "Retail Space",
                                "Warehouse",
                                "Restaurant",
                            ]
                        ),
                    )
                    db.add(commercial)

                # Create agent listing
                listing = AgentListing(
                    tax_id=tax_id,
                    property_address=address,
                    agent_nrds=random.choice(agents).nrds,
                    client_ssn=random.choice(clients).ssn,
                    l_agent_role=random.choice(list(AgentRole)),
                    listing_date=datetime.now(),
                    exclusive=random.choice([True, False]),
                )
                db.add(listing)
                properties_created += 1

            except Exception as e:
                print(f"Error creating property {i}: {e}")
                db.rollback()
                continue

            if (i + 1) % 5 == 0:
                try:
                    db.commit()
                    print(f"Committed batch of 5 properties ({i + 1}/{len(images)})")
                except Exception as e:
                    print(f"Error committing batch: {e}")
                    db.rollback()

        # Final commit
        try:
            db.commit()
        except Exception as e:
            print(f"Error in final commit: {e}")
            db.rollback()

        print("\nData generation completed!")
        print(f"Properties created: {properties_created}")

        # Verify data
        verification = {
            "Properties": db.query(Property).count(),
            "Residential": db.query(ResidentialProperty).count(),
            "Commercial": db.query(CommercialProperty).count(),
            "Listings": db.query(AgentListing).count(),
            "Agents": db.query(Agent).count(),
            "Clients": db.query(Client).count(),
        }

        print("\nDatabase verification:")
        for key, count in verification.items():
            print(f"{key}: {count}")

    except Exception as e:
        print(f"Error during data generation: {e}")
        db.rollback()
        raise


if __name__ == "__main__":
    db = SessionLocal()
    try:
        generate_sample_data(db)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        db.close()
