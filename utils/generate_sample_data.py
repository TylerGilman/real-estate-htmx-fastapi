import os
from dotenv import load_dotenv
import os
from dotenv import load_dotenv
from pexels_api import API
from sqlalchemy.orm import Session
from database import SessionLocal
from models import (
    Brokerage, 
    Agent, 
    Property, 
    PropertyType,
    ResidentialProperty,
    CommercialProperty,
    AgentListing,
    AgentRole,
    Client,
    ClientType
)

import random
from init_db import init_db
from faker import Faker

load_dotenv()
fake = Faker()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
if not PEXELS_API_KEY:
    raise ValueError("Please set the PEXELS_API_KEY in your .env file")

pexels = API(PEXELS_API_KEY)

def get_house_images(count: int = 50):
    print("Getting images...")
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
    print(f"Got {len(images)} images")
    return images[:count]

def create_brokerage(db: Session):
    print("Creating brokerage...")
    try:
        brokerage = Brokerage(
            broker_name="Cherokee Street Real Estate",
            broker_address="123 Cherokee Street",
            broker_phone="(555) 123-4567"
        )
        db.add(brokerage)
        db.commit()
        db.refresh(brokerage)
        print("Brokerage created successfully!")
        return brokerage
    except Exception as e:
        db.rollback()
        print(f"Error creating brokerage: {e}")
        raise

def create_agents(db: Session, brokerage_id: int, count: int = 5):
    print(f"Creating {count} agents...")
    agents = []
    for i in range(count):
        agent_name = fake.name()
        agent_phone = f"(555) 555-{random.randint(1000,9999):04d}"
        agent = Agent(
            agent_name=agent_name,
            agent_phone=agent_phone,
            nrds=f"NRDS{100000 + i}",
            ssn=f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}",
            broker_id=brokerage_id
        )
        db.add(agent)
        agents.append(agent)
    
    try:
        db.commit()
        print("Agents created successfully!")
        return agents
    except Exception as e:
        db.rollback()
        print(f"Error creating agents: {e}")
        raise

def generate_tax_id():
    return f"TAX{random.randint(100000, 999999)}"


# Function to create clients
def create_clients(db: Session, count: int = 10):
    print(f"Creating {count} clients...")
    clients = []
    for i in range(count):
        client_name = fake.name()
        client_phone = f"(555) 000-{random.randint(1000,9999):04d}"
        mailing_address = fake.address()
        ssn = f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
        client_type = random.choice(list(ClientType))

        client = Client(
            client_phone=client_phone,
            client_name=client_name,
            mailing_address=mailing_address,
            ssn=ssn,
            client_type=client_type
        )
        db.add(client)
        clients.append(client)

    try:
        db.commit()
        print("Clients created successfully!")
        return clients
    except Exception as e:
        db.rollback()
        print(f"Error creating clients: {e}")
        raise

# Modify create_properties to associate each property with a client
def create_properties(db: Session, agents: list, images: list, clients: list):
    print("Creating properties...")
    
    residential_types = ["Single Family", "Condo", "Townhouse", "Apartment"]
    commercial_types = ["Office Building", "Retail Space", "Warehouse", "Restaurant"]
    industries = ["Retail", "Office", "Industrial", "Mixed Use"]
    statuses = ["For Sale", "For Lease"]
    
    properties_created = 0
    
    for image in images:
        try:
            # Generate basic property info
            tax_id = generate_tax_id()
            address = fake.street_address()
            price = random.randint(200000, 1500000)
            status = random.choice(statuses)
            is_residential = random.choice([True, False])
            
            # Create base property
            property = Property(
                tax_id=tax_id,
                property_address=address,
                price=price,
                status=status,
                property_type=PropertyType.RESIDENTIAL if is_residential else PropertyType.COMMERCIAL,
                image_url=image["url"],
                image_width=image["width"],
                image_height=image["height"]
            )
            db.add(property)
            db.flush()
            
            # Add type-specific details
            if is_residential:
                residential = ResidentialProperty(
                    tax_id=tax_id,
                    property_address=address,
                    bedrooms=random.randint(1, 6),
                    bathrooms=random.choice([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]),
                    r_type=random.choice(residential_types)
                )
                db.add(residential)
            else:
                commercial = CommercialProperty(
                    tax_id=tax_id,
                    property_address=address,
                    sqft=random.randint(1000, 10000),
                    industry=random.choice(industries),
                    c_type=random.choice(commercial_types)
                )
                db.add(commercial)
            
            # Associate a random client with the property
            client = random.choice(clients)
            property.clients.append(client)
            
            # Create agent listing
            agent = random.choice(agents)
            agent_listing = AgentListing(
                tax_id=tax_id,
                property_address=address,
                agent_name=agent.agent_name,
                agent_phone=agent.agent_phone,
                client_phone=client.client_phone,  # Use the associated client’s phone
                l_agent_role=AgentRole.SELLER,
                exclusive=random.choice([True, False])
            )
            db.add(agent_listing)
            
            properties_created += 1
            
            # Commit every 10 properties
            if properties_created % 10 == 0:
                db.commit()
                print(f"Created {properties_created} properties...")
            
        except Exception as e:
            db.rollback()
            print(f"Error creating property: {e}")
            continue
    
    # Final commit for any remaining properties
    try:
        db.commit()
        print(f"Successfully created {properties_created} properties!")
    except Exception as e:
        db.rollback()
        print(f"Error in final commit: {e}")
        raise

def generate_sample_data():
    print("Starting sample data generation...")
    
    # Initialize database
    init_db()
    
    db = SessionLocal()
    try:
        # Create brokerage
        brokerage = create_brokerage(db)
        
        # Create agents
        agents = create_agents(db, brokerage.broker_id)
        
        # Create clients
        clients = create_clients(db, 10)
        
        # Get images for properties
        images = get_house_images(50)
        
        # Create properties with associated clients
        create_properties(db, agents, images, clients)
        
        print("Sample data generation completed successfully!")
        
    except Exception as e:
        print(f"Error during data generation: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    # Remove existing database if it exists
    if os.path.exists("real_estate.db"):
        os.remove("real_estate.db")
        print("Removed existing database")
    
    generate_sample_data()
