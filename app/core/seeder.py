from sqlalchemy.orm import Session
from app.models.service import Service

SEED_SERVICES = [
    # 1. Hair Cut (stock: 14)
    {
        "title": "Executive Men's Haircut & Grooming",
        "category": "hair cut",
        "description": "Premium scissor haircut, beard contouring, and mint scalp massage at your doorstep.",
        "price_bdt": 450.0,
        "stock": 14,
        "image_url": "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?w=600",
        "location_area": "Gulshan-2, Dhaka",
        "service_persons": 1,
        "rating": 0.0,
        "total_reviews": 0,
        "is_available": True
    },
    # 2. Makeup Beauty (stock: 8)
    {
        "title": "Bridal & Party Glam HD Makeup",
        "category": "makeup beauty",
        "description": "Full HD party makeup, false lash installation, saree draping, and setting spray.",
        "price_bdt": 3500.0,
        "stock": 8,
        "image_url": "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=600",
        "location_area": "Dhanmondi, Dhaka",
        "service_persons": 2,
        "rating": 0.0,
        "total_reviews": 0,
        "is_available": True
    },
    # 3. AC Repair (stock: 14)
    {
        "title": "Master AC Jet Chemical Wash & Gas Refill",
        "category": "ac repair",
        "description": "High pressure jet cleaning for indoor and outdoor coils, gas pressure measurement, and drain pipe cleaning.",
        "price_bdt": 1800.0,
        "stock": 14,
        "image_url": "https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=600",
        "location_area": "Mirpur DOHS, Dhaka",
        "service_persons": 2,
        "rating": 0.0,
        "total_reviews": 0,
        "is_available": True
    },
    # 4. House Painting (stock: 8)
    {
        "title": "Interior Luxury Wall Painting & Weather Coat",
        "category": "house painting",
        "description": "Full home wall putty scraping, waterproofing primer, and 2-coat luxury plastic emulsion.",
        "price_bdt": 12500.0,
        "stock": 8,
        "image_url": "https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=600",
        "location_area": "Banani, Dhaka",
        "service_persons": 3,
        "rating": 0.0,
        "total_reviews": 0,
        "is_available": True
    }
]

def seed_default_services(db: Session):
    service_count = db.query(Service).count()
    if service_count == 0:
        print(">>> [SEEDER] Inserting initial Bangladeshi services into database...")
        for item in SEED_SERVICES:
            db.add(Service(**item))
        db.commit()
        print(">>> [SEEDER] Initial services successfully added!")
    else:
        print(f">>> [SEEDER] Database already contains {service_count} services. Skipping seeding.")