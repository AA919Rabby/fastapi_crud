from sqlalchemy.orm import Session
from app.models.service import Service

SEED_SERVICES = [
    # 1. Hair Cut (stock: 14)
    {
        "title": "Executive Men's Haircut & Grooming",
        "category": "hair cut",
        "description": "Premium doorstep men's grooming service including a professionally styled scissor haircut, beard contouring and trimming, neckline cleanup, sideburn shaping, detailed finishing, and a refreshing mint scalp massage. Our experienced barber focuses on your preferred hairstyle, face shape, and personal style to provide a clean, comfortable, and polished grooming experience at your home.",
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
        "description": "Complete professional HD makeup service designed for bridal events, weddings, parties, and special occasions. The service includes skin preparation, HD foundation, professional eye makeup, false lash installation, contouring, highlighting, lip styling, setting spray, and elegant saree draping. Our makeup artist carefully matches the makeup style with your outfit, event, and personal preference for a long-lasting and polished look.",
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
        "description": "Professional AC maintenance service covering high-pressure jet cleaning of indoor and outdoor coils, removal of accumulated dust and dirt, gas pressure measurement, gas refill when required, drain pipe cleaning, and basic cooling performance inspection. The service is designed to improve airflow, maintain cooling performance, reduce common AC problems, and keep your air conditioner working efficiently.",
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
        "description": "Complete interior wall painting service for homes, apartments, and selected residential spaces. The service includes wall inspection, old paint and putty scraping where required, surface preparation, minor wall correction, waterproofing primer application, and two professional coats of luxury plastic emulsion. Our painting team focuses on smooth finishing, clean edges, proper surface coverage, and a neat final appearance while protecting your furniture and surrounding areas during the work.",
        "price_bdt": 12500.0,
        "stock": 8,
        "image_url": "https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=600",
        "location_area": "Banani, Dhaka",
        "service_persons": 3,
        "rating": 0.0,
        "total_reviews": 0,
        "is_available": True
    },

    # 5. Hair Cut (stock: 10)
    {
        "title": "Classic Men's Haircut & Beard Styling",
        "category": "hair cut",
        "description": "Convenient doorstep classic haircut and beard styling service for men who prefer a clean and professional appearance. The service includes a customized haircut based on your preferred length and style, beard trimming, beard shaping, neckline cleanup, sideburn detailing, and final styling. Our barber takes time to understand your preferred look and provides a comfortable grooming experience using professional tools and techniques.",
        "price_bdt": 550.0,
        "stock": 10,
        "image_url": "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?w=600",
        "location_area": "Uttara Sector-7, Dhaka",
        "service_persons": 1,
        "rating": 0.0,
        "total_reviews": 0,
        "is_available": True
    },

    # 6. Hair Cut (stock: 12)
    {
        "title": "Premium Fade Haircut & Beard Care",
        "category": "hair cut",
        "description": "Premium modern men's grooming service specializing in fade haircuts and detailed beard care. The service includes a customized fade haircut, precise blending around the sides and back, beard trimming and shaping, neckline detailing, sideburn cleanup, hair styling, and a refreshing finishing treatment. Suitable for customers looking for a modern, sharp, and well-maintained hairstyle with professional beard grooming at their preferred location.",
        "price_bdt": 700.0,
        "stock": 12,
        "image_url": "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?w=600",
        "location_area": "Mohammadpur, Dhaka",
        "service_persons": 2,
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