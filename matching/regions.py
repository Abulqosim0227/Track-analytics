REGIONS = {
    "Toshkent": (41.2995, 69.2401),
    "Toshkent viloyati": (41.0058, 69.6447),
    "Andijon": (40.7821, 72.3442),
    "Namangan": (40.9983, 71.6726),
    "Fargona": (40.3864, 71.7864),
    "Sirdaryo": (40.3864, 68.6614),
    "Jizzax": (40.1158, 67.8422),
    "Samarqand": (39.6270, 66.9750),
    "Qashqadaryo": (38.8610, 65.7890),
    "Surxondaryo": (37.9409, 67.5708),
    "Buxoro": (39.7680, 64.4210),
    "Navoiy": (40.0844, 65.3792),
    "Xorazm": (41.5500, 60.6314),
    "Qoraqalpogiston": (42.4600, 59.6100),
}

ADJACENCY = {
    "Toshkent": {"Toshkent viloyati", "Sirdaryo"},
    "Toshkent viloyati": {"Toshkent", "Sirdaryo", "Namangan"},
    "Andijon": {"Namangan", "Fargona"},
    "Namangan": {"Andijon", "Fargona", "Toshkent viloyati"},
    "Fargona": {"Andijon", "Namangan"},
    "Sirdaryo": {"Toshkent", "Toshkent viloyati", "Jizzax"},
    "Jizzax": {"Sirdaryo", "Samarqand"},
    "Samarqand": {"Jizzax", "Qashqadaryo", "Navoiy"},
    "Qashqadaryo": {"Samarqand", "Surxondaryo", "Buxoro"},
    "Surxondaryo": {"Qashqadaryo"},
    "Buxoro": {"Navoiy", "Qashqadaryo"},
    "Navoiy": {"Buxoro", "Samarqand", "Xorazm"},
    "Xorazm": {"Navoiy", "Qoraqalpogiston"},
    "Qoraqalpogiston": {"Xorazm"},
}

REGION_NAMES = list(REGIONS.keys())
