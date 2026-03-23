

from model import Recipe as DbRecipe


def create_recipe(db, title, ingredients, instructions, status, cuisine_type,preparation_time,serving_size):
    db_recipe = DbRecipe(
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
    return db.query(DbRecipe).all()


def update_recipe(db, id, title, ingredients, instructions, status, cuisine_type, preparation_time, serving_size):
    db_recipe = db.query(DbRecipe).filter(DbRecipe.id == id).first()
    if db_recipe:
        # Only overwrite columns that were provided (None = leave existing value).
        if title is not None:
            db_recipe.title = title
        if ingredients is not None:
            db_recipe.ingredients = ingredients
        if instructions is not None:
            db_recipe.instructions = instructions
        if status is not None:
            db_recipe.status = status
        if cuisine_type is not None:
            db_recipe.cuisine_type = cuisine_type
        if preparation_time is not None:
            db_recipe.preparation_time = preparation_time
        if serving_size is not None:
            db_recipe.serving_size = serving_size
        db.commit()
        db.refresh(db_recipe)
    return db_recipe


def delete_recipe(db, recipe_id: int):
    db_recipe = db.query(DbRecipe).filter(DbRecipe.id == recipe_id).first()
    if db_recipe:
        db.delete(db_recipe)
        db.commit()
    return db_recipe

def search_recipes(db, query: str):
    return db.query(DbRecipe).filter(
        (DbRecipe.title.ilike(f"%{query}%")) |
        (DbRecipe.ingredients.ilike(f"%{query}%")) |
        (DbRecipe.cuisine_type.ilike(f"%{query}%"))
    ).all()


def _escape_like_pattern(s: str) -> str:
    """Escape % and _ for SQL LIKE/ILIKE when using an escape char."""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def get_recipe_by_name(db, name: str):
    """
    Find one recipe by title: exact (case-insensitive), then partial title match.
    """
    name_clean = (name or "").strip()
    if not name_clean:
        return None

    # 1) Exact match (case-insensitive)
    exact = (
        db.query(DbRecipe)
        .filter(DbRecipe.title.ilike(name_clean))
        .first()
    )
    if exact:
        return exact

    # 2) Partial match, e.g. user says "chicken burger" vs DB "Chicken Burger Deluxe"
    safe = _escape_like_pattern(name_clean)
    pattern = f"%{safe}%"
    partial = (
        db.query(DbRecipe)
        .filter(DbRecipe.title.ilike(pattern, escape="\\"))
        .first()
    )
    return partial
