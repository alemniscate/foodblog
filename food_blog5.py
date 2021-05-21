import sqlite3
import sys

def create_db(filename):
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    cur.execute("CREATE TABLE IF NOT EXISTS meals(" +
                "meal_id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                "meal_name TEXT NOT NULL UNIQUE);")
    cur.execute("CREATE TABLE IF NOT EXISTS ingredients(" +
                "ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                "ingredient_name TEXT NOT NULL UNIQUE);")
    cur.execute("CREATE TABLE IF NOT EXISTS measures(" +
                "measure_id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                "measure_name TEXT UNIQUE);")
    cur.execute("CREATE TABLE IF NOT EXISTS recipes(" +
                "recipe_id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                "recipe_name TEXT NOT NULL, " +
                "recipe_description TEXT);")
    cur.execute("CREATE TABLE IF NOT EXISTS serve(" +
                "serve_id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                "meal_id INTEGER NOT NULL, " +
                "recipe_id INTEGER NOT NULL, " +
                "FOREIGN KEY(meal_id) REFERENCES meals(meal_id), " +
                "FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id));")
    cur.execute("CREATE TABLE IF NOT EXISTS quantity(" +
                "quantity_id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                "quantity INTEGER NOT NULL, " +
                "recipe_id INTEGER NOT NULL, " +
                "measure_id INTEGER NOT NULL, " +
                "ingredient_id INTEGER NOT NULL, " +
                "FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id), " +
                "FOREIGN KEY(measure_id) REFERENCES measures(measure_id), " +
                "FOREIGN KEY(ingredient_id) REFERENCES ingredients(ingredient_id));")
    conn.commit()
    return conn

def write_db(conn, table, name, value):
    cur = conn.cursor()
    cur.execute(f"INSERT INTO {table} ({name}) VALUES ({value});")
    conn.commit()

def write_db_tuple(conn, table, name, value):
    cur = conn.cursor()
    id = cur.execute(f"INSERT INTO {table} {name} VALUES {value};").lastrowid
    conn.commit()
    return id

def query_db(conn, table, name, pattern):
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM {table} WHERE {name} LIKE {pattern}')
    try:
        rs = cur.fetchall()
    except TypeError:
        return []
    return rs

def print_meals(conn):
    cur = conn.cursor()
    rs = cur.execute(f"SELECT * FROM meals;")
    for meal in rs.fetchall():
        meal_id, meal_name = meal
        print(f"{meal_id}) {meal_name}  ", end="")
    print()

def write_db_recipe(conn, recipe_name, recipe_description, meals):
    recipe_id = int(write_db_tuple(conn, "recipes", ("recipe_name", "recipe_description"), (f"'{recipe_name}'", f"'{recipe_description}'"))) 
    for meal_id in meals.split():
        write_db_tuple(conn, "serve", ("meal_id", "recipe_id"), (int(meal_id), recipe_id))
    return recipe_id

def write_db_quantity(conn, recipe_id, quantity_suit):
    strs = quantity_suit.split()
    if len(strs) == 2:
        quantity, ingredient_name = quantity_suit.split()
        measure_name = ""
    else:
        quantity, measure_name, ingredient_name = quantity_suit.split()
    quantity = int(quantity)
    if measure_name == "":
        rs = query_db(conn, "measures", "measure_name", f"''")
    else:
        rs = query_db(conn, "measures", "measure_name", f"'%{measure_name}%'")
    if len(rs) != 1:
        print("The measure is not conclusive!")
        return
    measure_id = rs[0][0]
    rs = query_db(conn, "ingredients", "ingredient_name", f"'%{ingredient_name}%'")
    if len(rs) != 1:
        print("The ingredient is not conclusive!")
        return
    ingredient_id = rs[0][0]
    write_db_tuple(conn, "quantity", ("quantity", "recipe_id", "measure_id", "ingredient_id"), (quantity, recipe_id, measure_id, ingredient_id))

def create(filename):

    data = {"meals": ("breakfast", "brunch", "lunch", "supper"),
            "ingredients": ("milk", "cacao", "strawberry", "blueberry", "blackberry", "sugar"),
            "measures": ("ml", "g", "l", "cup", "tbsp", "tsp", "dsp", "")}

    conn = create_db(filename)
    for table in data:
        name = table[:len(table) - 1] + "_name"
        values = data[table]
        for value in values:
            write_db(conn, table, name, f"'{value}'")
    print("Pass the empty recipe name to exit.")
    while True:
        recipe_name = input("Recipe name: ")
        if recipe_name == "":
            break 
        recipe_description = input("Recipe description: ")
        print_meals(conn)
        meals = input("Enter proposed meals separated by a space: ")
        recipe_id = write_db_recipe(conn, recipe_name, recipe_description, meals)
        while True:
            quantity = input("Input quantity of ingredient <press enter to stop>: ")
            if quantity == "":
                break
            write_db_quantity(conn, recipe_id, quantity)
    conn.close()

def query_ingredients(conn, ingredients):
    cur = conn.cursor()
    ingredients_tuple = tuple(ingredients) if len(ingredients) > 1 else f"('{ingredients[0]}')"
    cur.execute(f"SELECT ingredient_id FROM ingredients WHERE ingredient_name in {ingredients_tuple}")
    try:
        rs = [x[0] for x in cur.fetchall()]
    except TypeError:
        return []
    return rs

def query_meals(conn, meals):
    cur = conn.cursor()
    meals_tuple = tuple(meals) if len(meals) > 1 else f"('{meals[0]}')"
    cur.execute(f"SELECT meal_id FROM meals WHERE meal_name IN {meals_tuple}")
    try:
        rs = [x[0] for x in cur.fetchall()]
    except TypeError:
        return []
    return rs
    
def query_quantity(conn, ingredient_id):
    cur = conn.cursor()
    cur.execute(f"SELECT DISTINCT recipe_id FROM quantity WHERE ingredient_id = '{ingredient_id}'")
    try:
        rs = [x[0] for x in cur.fetchall()]
    except TypeError:
        return []
    return rs

def query_serve(conn, meals_id):
    cur = conn.cursor()
    meals_tuple = tuple(meals_id) if len(meals_id) > 1 else f"({meals_id[0]})"
    cur.execute(f"SELECT DISTINCT recipe_id FROM serve WHERE meal_id IN {meals_tuple}")
    try:
        rs = [x[0] for x in cur.fetchall()]
    except TypeError:
        return []
    return rs

def query_recipe(conn, recipes_id):
    cur = conn.cursor()
    recipes_tuple = tuple(recipes_id) if len(recipes_id) > 1 else f"({recipes_id[0]})"
    cur.execute(f"SELECT recipe_name FROM recipes WHERE recipe_id IN {recipes_tuple}")
    try:
        rs = [x[0].strip("'") for x in cur.fetchall()]
    except TypeError:
        return []
    return rs

def count_db(conn, table):
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT( * ) FROM {table}")
    try:
       rs = cur.fetchone()[0]
    except TypeError:
       return 0
    return rs

def query(filname, ingredients, meals):
    conn = sqlite3.connect(filename)
    ingredients_id = query_ingredients(conn, ingredients)
    if len(ingredients_id) != len(ingredients):
        print("There are no such recipes in the database.")
        return      
    recipes_id = set(range(1, count_db(conn, 'recipes') + 1))
    for id in ingredients_id:    
        recipes_id = recipes_id.intersection(set(query_quantity(conn, id)))
    meals_id = query_meals(conn, meals)
    recipes_id2 = query_serve(conn, meals_id)
    recipes_id3 = set(recipes_id).intersection(set(recipes_id2))
    if len(recipes_id3) == 0:
        print("There are no such recipes in the database.")
    else:
        recipes_name = query_recipe(conn, list(recipes_id3))
        print("Recipes selected for you:", ", ".join(recipes_name))
    conn.close()

def parsearg():
    filename = sys.argv[1]
    ingredients = None
    meals = None
    for arg in sys.argv:
        if arg.startswith("--ingredients="):
            ingredients = arg[len("--ingredients="):].strip('"').split(",")
        elif arg.startswith("--meals="):
            meals = arg[len("--meals="):].strip('"').split(",")
    return filename, ingredients, meals


filename, ingredients, meals = parsearg()
# filename = "food_blog.db"
# ingredients =["sugar","milk"]
# meals=["breakfast","brunch"]
# ingredients=["cacao"]
# meals=["brunch","supper"]
# ingredients = ['strawberry', 'cheese']
# meals = ['supper']

print(ingredients)
print(meals)

if ingredients and meals:
    query(filename, ingredients, meals)
else:
    create(filename)
