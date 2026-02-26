import random
from AstroDatabase import DatabaseManager

def seed_data(count=100):
    service = DatabaseManager()
    prefixes = ["Messier", "M", "NGC", "IC", "C", "Caldwell", "Herschel", "Sh2", "RCW", "Gum", "vdb",
    "Barnard", "B", "Abell", "Arp", "VV", "HCG", "UGC", "PGC", "MCG", "ESO", "Zwicky", 
    "CGCG", "Markarian", "Mrk", "VCC", "AM", "Arak", "KPG", "Kar", "DDO", "DW",]
    objects = [
    "Emission Nebula", "Reflection Nebula", "Dark Nebula", "Planetary Nebula", 
    "Supernova Remnant", "H II Region", "Molecular Cloud", "Herbig-Haro Object",
    "Star Cluster", "Open Cluster", "Globular Cluster", "Stellar Association",
    "Protostar", "Main Sequence Star", "Red Giant", "White Dwarf", "Neutron Star", 
    "Pulsar", "Magnetar", "Black Hole", "Microquasar", "Brown Dwarf",

    "Galaxy", "Spiral Galaxy", "Elliptical Galaxy", "Lenticular Galaxy", 
    "Irregular Galaxy", "Dwarf Galaxy", "Starburst Galaxy", "Active Galactic Nucleus",
    "Seyfert Galaxy", "Quasar", "Blazar", "Radio Galaxy", "Galaxy Cluster", 
    "Galaxy Group", "Supercluster", "Void", "Gravitational Lens",

    "Exoplanet", "Hot Jupiter", "Super-Earth", "Protoplanetary Disk", "Asteroid", 
    "Comet", "Centaur", "Kuiper Belt Object", "Trans-Neptunian Object"
]
    print(f"Ξεκινάει η προσθήκη {count} εγγραφών...")

    for i in range(count):
        name = f"{random.choice(prefixes)} {random.randint(1, 8000)} {random.choice(objects)}"
        ra = f"{random.randint(0, 23):02}h {random.randint(0, 59):02}m {random.randint(0, 59):02}s"
        dec = f"{random.choice(['', '-'])}{random.randint(0, 89):02}° {random.randint(0, 59):02}' {random.randint(0,59):02}''"
        notes_list = [
            "Clear skies, excellent visibility.",
            "Slight light pollution from the city.",
            "Used a 10-inch Dobsonian telescope.",
            "Observation during new moon.",
            "Very faint, required averted vision.",
            ""
        ]
        notes = random.choice(notes_list)
        service.add_observation(name, ra, dec, notes)
        
        if (i + 1) % 10 == 0:
            print(f"Προστέθηκαν {i + 1} εγγραφές...")

    print("Η σπορά δεδομένων ολοκληρώθηκε επιτυχώς!")

if __name__ == "__main__":
    seed_data(100000000)