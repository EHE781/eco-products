"""
Seed PostgreSQL with the initial food product catalogue.
Run once after creating the DB:
    cd backend
    python seed.py
"""
from app.database import SessionLocal, init_db
from app.models import Product, ProductBenefit, ProductCert

# Food-only catalogue (Alimentación, Lácteos, Panadería, Bebidas)
# Cosmética and Limpieza excluded — too much variety, different data model
PRODUCTS = [
    {"id": 1, "name_es": "Manzanas Bio Fuji", "name_en": "Bio Fuji Apples", "name_ca": "Pomes Bio Fuji", "cat": "Alimentación", "origin": "Lleida, Catalunya", "lat": 41.6176, "lon": 0.6200, "price": 3.20, "unit": "kg", "ns": "A", "es_score": "A", "emoji": "🍎", "season": "Sep–Mar", "year_round": False, "co2": 0.9, "desc_es": "Cultivadas sin pesticidas en la huerta leridana. Transporte en furgoneta eléctrica.", "desc_en": "Grown without pesticides in Lleida's orchards. Transported by electric van.", "desc_ca": "Cultivades sense pesticides a l'horta lleidatana. Transport en furgoneta elèctrica.", "certs": {"es": ["Bio", "Recogida a mano"], "en": ["Bio", "Hand-picked"], "ca": ["Bio", "Collida a mà"]}, "bens": {"es": ["Alto en fibra", "Sin pesticidas", "Recogida esta semana"], "en": ["High in fibre", "Pesticide-free", "Harvested this week"], "ca": ["Alt en fibra", "Sense pesticides", "Collita d'aquesta setmana"]}},
    {"id": 2, "name_es": "Pan de Espelta Artesano", "name_en": "Artisan Spelt Bread", "name_ca": "Pa d'Espelta Artesà", "cat": "Panadería", "origin": "Gracia, Barcelona", "lat": 41.4033, "lon": 2.1563, "price": 4.50, "unit": "ud", "ns": "A", "es_score": "A", "emoji": "🍞", "season": "Todo el año", "year_round": True, "co2": 1.2, "desc_es": "Elaborado a diario con espelta ecológica, fermentación de 18h y cocción en horno de piedra.", "desc_en": "Made daily with organic spelt, 18h fermentation and stone oven baking.", "desc_ca": "Elaborat diàriament amb espelta ecològica, fermentació de 18h i cocció en forn de pedra.", "certs": {"es": ["Km0", "Artesano", "Sin aditivos"], "en": ["Km0", "Artisan", "No additives"], "ca": ["Km0", "Artesà", "Sense additius"]}, "bens": {"es": ["Fermentación larga", "Harina integral local", "Sin conservantes"], "en": ["Long fermentation", "Local wholemeal flour", "No preservatives"], "ca": ["Fermentació llarga", "Farina integral local", "Sense conservants"]}},
    {"id": 3, "name_es": "Yogur Natural Bio", "name_en": "Bio Natural Yoghurt", "name_ca": "Iogurt Natural Bio", "cat": "Lácteos", "origin": "Osona, Barcelona", "lat": 41.9302, "lon": 2.2548, "price": 1.80, "unit": "ud", "ns": "A", "es_score": "A", "emoji": "🥛", "season": "Todo el año", "year_round": True, "co2": 0.5, "desc_es": "Leche fresca de vacas en pastoreo extensivo en Osona, sin espesantes ni aromas.", "desc_en": "Fresh milk from free-range cows in Osona, no thickeners or flavourings.", "desc_ca": "Llet fresca de vaques en pasturatge extensiu a Osona, sense espessants ni aromes.", "certs": {"es": ["Bio", "Pastoreo", "Certificado"], "en": ["Bio", "Free-range", "Certified"], "ca": ["Bio", "Pasturatge", "Certificat"]}, "bens": {"es": ["Vacas en pastoreo", "Sin azúcares añadidos", "Probióticos naturales"], "en": ["Free-range cows", "No added sugars", "Natural probiotics"], "ca": ["Vaques en pasturatge", "Sense sucres afegits", "Probiòtics naturals"]}},
    {"id": 4, "name_es": "Aceite de Oliva Virgen Extra", "name_en": "Extra Virgin Olive Oil", "name_ca": "Oli d'Oliva Verge Extra", "cat": "Alimentación", "origin": "Baena, Córdoba", "lat": 37.6166, "lon": -4.3167, "price": 8.90, "unit": "500ml", "ns": "B", "es_score": "A", "emoji": "🫒", "season": "Nov–Feb", "year_round": False, "co2": 0.3, "desc_es": "Picual de cosecha temprana, primera prensa en frío.", "desc_en": "Early harvest Picual, first cold press.", "desc_ca": "Picual de collita primerenca, primera premsa en fred.", "certs": {"es": ["Bio", "DO Baena", "Prensa fría"], "en": ["Bio", "DO Baena", "Cold press"], "ca": ["Bio", "DO Baena", "Premsa freda"]}, "bens": {"es": ["Grasas saludables", "Polifenoles", "DO protegida"], "en": ["Healthy fats", "Polyphenols", "Protected designation"], "ca": ["Greixos saludables", "Polifenols", "DO protegida"]}},
    {"id": 5, "name_es": "Bebida de Almendras", "name_en": "Almond Drink", "name_ca": "Beguda d'Ametlles", "cat": "Bebidas", "origin": "Camp de Tarragona", "lat": 41.1189, "lon": 1.2445, "price": 2.40, "unit": "litro", "ns": "B", "es_score": "A", "emoji": "🌰", "season": "Todo el año", "year_round": True, "co2": 0.7, "desc_es": "Elaborada con almendras del Camp de Tarragona, sin carragenanos ni azúcares.", "desc_en": "Made with almonds from Camp de Tarragona, no carrageenan or sugars.", "desc_ca": "Elaborada amb ametlles del Camp de Tarragona, sense carragenans ni sucres.", "certs": {"es": ["Bio", "Sin azúcar", "Local"], "en": ["Bio", "No sugar", "Local"], "ca": ["Bio", "Sense sucre", "Local"]}, "bens": {"es": ["Bajo en calorías", "Sin lactosa", "Almendras locales"], "en": ["Low calorie", "Lactose-free", "Local almonds"], "ca": ["Baix en calories", "Sense lactosa", "Ametlles locals"]}},
    {"id": 6, "name_es": "Tomates Cherry Bio", "name_en": "Bio Cherry Tomatoes", "name_ca": "Tomàquets Cherry Bio", "cat": "Alimentación", "origin": "Maresme, Barcelona", "lat": 41.5411, "lon": 2.4378, "price": 2.80, "unit": "250g", "ns": "A", "es_score": "A", "emoji": "🍅", "season": "Jun–Oct", "year_round": False, "co2": 1.0, "desc_es": "Cultivados al aire libre en el Maresme, recogidos en su punto óptimo de maduración.", "desc_en": "Grown outdoors in El Maresme, picked at peak ripeness.", "desc_ca": "Cultivats a l'aire lliure al Maresme, recollits en el seu punt òptim de maduració.", "certs": {"es": ["Bio", "Km Cercano", "Temporada"], "en": ["Bio", "Near Km", "Seasonal"], "ca": ["Bio", "Km Proper", "Temporada"]}, "bens": {"es": ["Licopeno natural", "Sin invernadero", "Sabor auténtico"], "en": ["Natural lycopene", "No greenhouse", "Authentic flavour"], "ca": ["Licopè natural", "Sense hivernacle", "Sabor autèntic"]}},
    {"id": 7, "name_es": "Miel Cruda de Collserola", "name_en": "Raw Collserola Honey", "name_ca": "Mel Crua de Collserola", "cat": "Alimentación", "origin": "Collserola, Barcelona", "lat": 41.4231, "lon": 2.0840, "price": 9.50, "unit": "500g", "ns": "C", "es_score": "A", "emoji": "🍯", "season": "Jul–Sep", "year_round": False, "co2": 0.8, "desc_es": "Extraída en frío del parque de Collserola, sin pasteurizar.", "desc_en": "Cold-extracted from Collserola park, unpasteurised.", "desc_ca": "Extreta en fred del parc de Collserola, sense pasteuritzar.", "certs": {"es": ["Bio", "Km0", "Sin filtrar"], "en": ["Bio", "Km0", "Unfiltered"], "ca": ["Bio", "Km0", "Sense filtrar"]}, "bens": {"es": ["Antioxidantes", "Enzimas activas", "Apoyo local"], "en": ["Antioxidants", "Active enzymes", "Local support"], "ca": ["Antioxidants", "Enzims actius", "Suport local"]}},
    {"id": 8, "name_es": "Granola Artesanal", "name_en": "Artisan Granola", "name_ca": "Granola Artesanal", "cat": "Panadería", "origin": "Sant Gervasi, Barcelona", "lat": 41.3944, "lon": 2.1337, "price": 5.60, "unit": "400g", "ns": "B", "es_score": "A", "emoji": "🌾", "season": "Todo el año", "year_round": True, "co2": 0.6, "desc_es": "Tostada al horno con avena integral ecológica, aceite de coco y frutos secos de proximidad.", "desc_en": "Oven-toasted with organic whole oats, coconut oil and local nuts.", "desc_ca": "Torrada al forn amb civada integral ecològica, oli de coco i fruits secs de proximitat.", "certs": {"es": ["Bio", "Artesano", "Sin palma"], "en": ["Bio", "Artisan", "Palm-free"], "ca": ["Bio", "Artesanal", "Sense palma"]}, "bens": {"es": ["Sin aceite de palma", "Copos integrales", "Frutos secos locales"], "en": ["No palm oil", "Whole flakes", "Local nuts"], "ca": ["Sense oli de palma", "Flocs integrals", "Fruits secs locals"]}},
    {"id": 9, "name_es": "Chocolate Negro 85%", "name_en": "85% Dark Chocolate", "name_ca": "Xocolata Negra 85%", "cat": "Alimentación", "origin": "Vic, Barcelona", "lat": 41.9302, "lon": 2.2548, "price": 3.90, "unit": "100g", "ns": "C", "es_score": "B", "emoji": "🍫", "season": "Todo el año", "year_round": True, "co2": 0.2, "desc_es": "Cacao de Ghana (Fairtrade), elaborado por chocolatería artesanal catalana.", "desc_en": "Fairtrade Ghana cacao, crafted by a Catalan artisan chocolatier.", "desc_ca": "Cacau de Ghana (Fairtrade), elaborat per una xocolateria artesana catalana.", "certs": {"es": ["Fairtrade", "Bio", "Sin lecitina"], "en": ["Fairtrade", "Bio", "No lecithin"], "ca": ["Fairtrade", "Bio", "Sense lecitina"]}, "bens": {"es": ["Alto en cacao", "Comercio justo", "Sin azúcar añadido"], "en": ["High cacao content", "Fair trade", "No added sugar"], "ca": ["Alt en cacau", "Comerç just", "Sense sucre afegit"]}},
    {"id": 13, "name_es": "Té Verde Sencha Orgánico", "name_en": "Organic Sencha Green Tea", "name_ca": "Te Verd Sencha Orgànic", "cat": "Bebidas", "origin": "Uji, Japón", "lat": 34.8844, "lon": 135.7997, "price": 7.80, "unit": "50g", "ns": "A", "es_score": "C", "emoji": "🍵", "season": "Abr–May", "year_round": False, "co2": -1.2, "desc_es": "Primera cosecha Uji, sin pesticidas.", "desc_en": "First harvest Uji, pesticide-free.", "desc_ca": "Primera collita Uji, sense pesticides.", "certs": {"es": ["Bio JAS", "Fairtrade"], "en": ["Bio JAS", "Fairtrade"], "ca": ["Bio JAS", "Fairtrade"]}, "bens": {"es": ["Alto en catequinas", "Certificación JAS", "Recolección manual"], "en": ["High in catechins", "JAS certification", "Hand-picked"], "ca": ["Alt en catequines", "Certificació JAS", "Recol·lecció manual"]}},
    {"id": 14, "name_es": "Pasta Integral Orgánica", "name_en": "Organic Wholemeal Pasta", "name_ca": "Pasta Integral Orgànica", "cat": "Alimentación", "origin": "Gragnano, Italia", "lat": 40.6952, "lon": 14.5218, "price": 3.10, "unit": "500g", "ns": "A", "es_score": "A", "emoji": "🍝", "season": "Todo el año", "year_round": True, "co2": 0.4, "desc_es": "Sémola de trigo duro ecológico, extrusión en bronce y secado lento 48h.", "desc_en": "Organic durum wheat semolina, bronze die extrusion and 48h slow drying.", "desc_ca": "Sèmola de blat dur ecològic, extrusió en bronze i assecat lent 48h.", "certs": {"es": ["Bio EU", "IGP Gragnano"], "en": ["Bio EU", "IGP Gragnano"], "ca": ["Bio EU", "IGP Gragnano"]}, "bens": {"es": ["Trigo duro bio", "Extrusión en bronce", "Secado lento"], "en": ["Bio durum wheat", "Bronze extrusion", "Slow dried"], "ca": ["Blat dur bio", "Extrusió en bronze", "Assecat lent"]}},
]


def seed():
    init_db()
    db = SessionLocal()
    try:
        db.query(ProductBenefit).delete()
        db.query(ProductCert).delete()
        db.query(Product).delete()
        db.commit()

        for p in PRODUCTS:
            product = Product(
                id=p["id"],
                name_es=p["name_es"], name_en=p["name_en"], name_ca=p["name_ca"],
                cat=p["cat"], origin=p["origin"],
                lat=p["lat"], lon=p["lon"],
                price=p["price"], unit=p["unit"],
                ns=p["ns"], es_score=p["es_score"],
                emoji=p["emoji"], season=p["season"],
                year_round=p["year_round"], co2=p["co2"],
                desc_es=p["desc_es"], desc_en=p["desc_en"], desc_ca=p["desc_ca"],
            )
            db.add(product)
            db.flush()

            for lang, certs in p["certs"].items():
                for cert in certs:
                    db.add(ProductCert(product_id=p["id"], lang=lang, cert=cert))

            for lang, bens in p["bens"].items():
                for i, ben in enumerate(bens):
                    db.add(ProductBenefit(product_id=p["id"], lang=lang, benefit=ben, position=i))

        db.commit()
        print(f"Seeded {len(PRODUCTS)} food products.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
