

from schema import Recipe


def create_recipe(db, title, ingredients, instructions, status, cuisine_type,preparation_time,serving_size):
    db_recipe = Recipe(
        title=title,
        ingredients=ingredients,
        instructions=instructions,
        status=status,
        cuisine_type=cuisine_type,
        preparation_time=preparation_time,
        serving_size=serving_size
    )
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe


def get_all_recipes(db):
    return db.query(Recipe).all()


def update_recipe(db, id, title, ingredients, instructions, status, cuisine_type, preparation_time, serving_size):
    db_recipe = db.query(Recipe).filter(Recipe.id == id).first()
    if db_recipe:
        db_recipe.title = title
        db_recipe.ingredients = ingredients
        db_recipe.instructions = instructions
        db_recipe.status = status
        db_recipe.cuisine_type = cuisine_type
        db_recipe.preparation_time = preparation_time
        db_recipe.serving_size = serving_size
        db.commit()
        db.refresh(db_recipe)
    return db_recipe


def delete_recipe(db, recipe_id: int):
    db_recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if db_recipe:
        db.delete(db_recipe)
        db.commit()
    return db_recipe

def search_recipes(db, query: str):
    return db.query(Recipe).filter(
        (Recipe.title.ilike(f"%{query}%")) |
        (Recipe.ingredients.ilike(f"%{query}%")) |
        (Recipe.cuisine_type.ilike(f"%{query}%"))
    ).all()