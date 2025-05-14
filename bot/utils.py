from difflib import get_close_matches

def find_closest_ingredients(user_ingredients, recipe_ingredients):
    """
    Returns the number of matching ingredients and the missing ones.
    """
    user_set = set([i.strip().lower() for i in user_ingredients])
    recipe_set = set([i.strip().lower() for i in recipe_ingredients])
    matches = user_set & recipe_set
    missing = recipe_set - user_set
    return len(matches), list(missing)

def format_recipe(recipe, missing_ingredients=None):
    msg = f"{recipe['title']}\nIngredients: {recipe['ingredients']}\nInstructions: {recipe['instructions']}"
    if missing_ingredients:
        msg += f"\nMissing ingredients: {', '.join(missing_ingredients)}"
    return msg 