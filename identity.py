import random

EG_FIRST_NAMES = [
    "Mohamed", "Ahmed", "Mahmoud", "Youssef", "Omar", 
    "Ali", "Hassan", "Ibrahim", "Mostafa", "Khaled", 
    "Amr", "Tarek", "Karim", "Sherif", "Hussein", 
    "Mina", "Adel", "Hisham", "Osama", "Walid",
    "Ziad", "Yasser", "Sameh", "Ramy", "Eslam", "Sobhy"
]

EG_LAST_NAMES = [
    "Ali", "Hassan", "Ibrahim", "Mohamed", "Ahmed", 
    "Mahmoud", "Saeed", "Hussain", "Fawzy",
    "Soliman", "Kamel", "Samir", "Sobhy", "Reda", "Farag", 
    "Gaber", "Nabil", "Khalil", "Mansour", "Zaki"
]

EU_FIRST_NAMES = [
    "James", "Oliver", "William", "Lucas", "Henry", 
    "Theodore", "Jack", "Levi", "Alexander", "Jacob", 
    "Thomas", "Daniel", "Matthew", "Joseph", "Samuel", 
    "David", "John", "Wyatt", "Luke", "Gabriel", 
    "Adam", "Benjamin", "Liam", "Noah", "Elijah", 
    "Arthur", "Felix", "Julian", "Silas", "Jasper", 
    "Finn", "Arlo", "Rowan", "Tobias", "Jude", 
    "Milo", "Ezra", "Leon", "Hugo", "Otto", 
    "Soren", "Elian", "Callum", "Kian", "Stellan", 
    "Leif", "Ewan", "Cillian", "Declan", "Ronan", 
    "Lorcan", "Alistair", "Lachlan", "Hamish", "Fraser", 
    "Tadhg", "Oisin", "Finnian", "Daithi", "Ruairi", 
    "Jarlath", "Fionn", "Tiernan", "Cathal", "Eoghan", 
    "Diarmuid", "Padraig", "Seamus", "Ciaran", "Niall", 
    "Aodhan", "Rian", "Odhran", "Senan", "Ultan", 
    "Fiachra", "Conall", "Eanna", "Darragh", "Eamon", 
    "Magnus", "Axel", "Bjorn", "Lars", "Sven", 
    "Niels", "Bram", "Floris", "Thijs", "Milan", 
    "Oscar", "Emil", "Anton", "Linus", "Rasmus", 
    "Mikkel", "Casper", "Mathias", 
    "Enzo", "Matteo", "Luca", "Leonardo", "Raphael", 
    "Louis", "Antoine", "Maxime", "Victor", "Jules", 
    "Theo", "Fabian", "Lucian", "Valerian", "Dorian", 
    "Filip", "Jakub", "Kacper", "Szymon", "Jan", 
    "Antoni", "Mikolaj", "Igor", "Tymon", "Jacek", 
    "Borys", "Nikolai", "Stefan", 
    "Zev", "Rafe", "Ivor", "Cormac", "Alaric", 
    "Bastian", "Cassian", "Evander", "Gideon", "Hayes", 
    "Idris", "Jace", "Kael", "Orson", "Phineas", 
    "Quentin", "Rhys", "Tristan", "Uri", "Weston", 
    "Xander", "Yves", "Zane", "Matthias", "Amias"
]

EU_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", 
    "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", 
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", 
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", 
    "Thompson", "White", "Harris", "Sanchez", "Clark", 
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", 
    "Allen", "King", "Wright", "Scott", "Torres", 
    "Hill", "Flores", "Green", "Adams", "Nelson", 
    "Baker", "Hall", "Rivera", "Campbell", "Mitchell", 
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", 
    "Turner", "Diaz", "Parker", "Cruz", "Edwards", 
    "Collins", "Reyes", "Stewart", "Morris", "Morales", 
    "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", 
    "Morgan", "Cooper", "Peterson", "Bailey", "Reed", 
    "Kelly", "Howard", "Ramos", "Cox", "Ward", 
    "Richardson", "Watson", "Brooks", "Chavez", "Wood", 
    "Bennett", "Gray", "Mendoza", "Ruiz", "Hughes", 
    "Price", "Alvarez", "Castillo", "Sanders", "Myers", 
    "Long", "Ross", "Foster", "Jimenez", "Powell", 
    "Jenkins", "Perry", "Russell", "Sullivan", "Bell", 
    "Coleman", "Butler", "Henderson", "Barnes", "Fisher", 
    "Vasquez", "Simmons", "Romero", "Jordan", "Patterson", 
    "Alexander", "Hamilton", "Graham", "Reynolds", "Griffin", 
    "Dubois", "Schmidt", "Muller", "Rossi", "Silva", 
    "Weber", "Meyer", "Wagner", "Becker", "Hoffmann"
]

def generate_identity(use_western_names=False):
    """
    Generates a realistic identity.
    - use_western_names=True: Returns English/European names (for VPN).
    - use_western_names=False: Returns Egyptian names (for Hardware).
    """
    
    if use_western_names:
        first = random.choice(EU_FIRST_NAMES)
        last = random.choice(EU_LAST_NAMES)
    else:
        first = random.choice(EG_FIRST_NAMES)
        last = random.choice(EG_LAST_NAMES)
    
    display_name = f"{first} {last}"
    
    separator = random.choice([".", "_", "", ""]) 
    
    digit_count = random.randint(3, 7)
    
    random_digits = "".join([str(random.randint(0, 9)) for _ in range(digit_count)])

    username = f"{first.lower()}{separator}{last.lower()}{random_digits}"

    password = f"{last}@{random_digits}#{first}"
    
    birth_year = random.randint(1996, 2006)

    return {
        "email": f"{username}@outlook.com", 
        "username": username,
        "display_name": display_name,
        "password": password,
        "day": str(random.randint(1, 28)),
        "month": random.choice(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]),
        "year": str(birth_year)
    }

if __name__ == "__main__":
    print("Western:", generate_identity(use_western_names=True))
    print("Egyptian:", generate_identity(use_western_names=False))
