""" APPLICATION CONSTANTS """

ALLERGENICS = ['nuts', 'eggs', 'orange', 'beef', 'yamaimo', 'crustaceans',
               'celery', 'lupin', 'none', 'gluten', 'red-caviar', 'kiwi', 
               'peanuts', 'matsutake', 'apple', 'banana', 'mustard', 
               'gelatin', 'peach', 'soybeans', 'chicken', 'molluscs', 
               'fish', 'sesame-seeds', 'sulphur-dioxide-and-sulphites',
               'milk', 'pork']

NUTRISCORE_GRADE = ['a', 'b', 'c', 'd', 'e']

FOOD_SAFTY_RANGES = {
    "sugars_100g": {
        "low": {"start": 0, "end": 5},
        "middle": {"start": 5, "end": 24},
        "high": {"start": 24},
    },
    "fat_100g": {
        "low": {"start": 0, "end": 3},
        "middle": {"start": 4, "end": 18},
        "high": {"start": 18},
    },
    "saturated-fat_100g": {
        "low": {"start": 0, "end": 1.5},
        "middle": {"start": 1.5, "end": 5},
        "high": {"start": 5},
    },
    "fiber_100g": {
        "low": {"start": 0, "end": 3},
        "middle": {"start": 3, "end": 6},
        "high": {"start": 6},
    },
    "salt_100g": {
        "low": {"start": 0, "end": 0.3},
        "middle": {"start": 0.3, "end": 1.5},
        "high": {"start": 1.5},
    },
}
