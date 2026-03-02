# Recipe_management
🍽️ AI-Powered Recipe Management System
An intelligent Recipe Management System built using Python, PostgreSQL, SQLAlchemy, and OpenAI Function Calling.

This application allows users to manage recipes using natural language commands powered by an AI agent.

Instead of traditional buttons and forms, users can type:

"Add a new Italian pasta recipe"
"Show me all favorite recipes"
"Update recipe 3 to mark it as made before"
"Delete recipe 5"
"search for a recipe"
The AI understands the intent, selects the correct backend function, executes it, and returns a natural language response.

🚀 Features
✅ Recipe Management (CRUD)
Create new recipes
Update existing recipes
Delete recipes
Retrieve all recipes
Search for a recipe
Each recipe includes:

Title
Ingredients
Instructions
Status (favorite, to try, made before)
Cuisine type
Preparation time
Serving size
🤖 AI Agent Integration
This project uses OpenAI Function Calling to:

Understand user intent
Select the correct backend function
Execute database operations
Return a human-readable response
The system implements a manual AI agent loop without using frameworks like LangChain.

🏗️ Architecture
User Input
↓
OpenAI Model (gpt-4o-mini)
↓
Tool Call (Function Calling)
↓
Backend CRUD Function
↓
PostgreSQL Database
↓
Tool Result returned to Model
↓
Final Natural Language Response

🛠️ Tech Stack
Python 3.10+
PostgreSQL
SQLAlchemy ORM
OpenAI API (Function Calling)
Gradio (UI)
🧠 AI Implementation Details
Defined AI tools:

create_recipe
update_recipe
delete_recipe
get_all_recipes
search_recipe
Agent flow:

Send user message to OpenAI
Model decides whether to call a tool
Backend executes the function
Tool result is sent back to the model
Model generates final natural language reply
This enables conversational CRUD operations over a relational database.

📦 Installation
1️⃣ Clone Repository
git clone https://github.com/zeinabkobaissi/Assessment_projects/Recipe-management.git
cd Recipe-management
2️⃣ Create Virtual Environment
python -m venv venv
venv\Scripts\activate
3️⃣ Install Dependencies
pip install -r requirements.txt
Example requirements:

openai
sqlalchemy
psycopg2-binary
gradio
python-dotenv
4️⃣ Configure Environment Variables
Create a .env file:

OPENAI_KEY=your_openai_api_key
DATABASE_URL=postgresql://username:password@localhost:5432/recipes_db
5️⃣ Run the Application
If using Gradio UI:

python gradio_UI.py
Or CLI version:

python main.py
🧪 Example Usage
Add a recipe:

Add a Lebanese tabbouleh recipe with parsley, tomato, bulgur and lemon.

Update a recipe:

Update recipe 2 and mark it as made before.

Retrieve recipes:

Show me all Italian recipes.

Delete a recipe:

Delete recipe 5.

Search for a recipe:

Search for a meal that ingredients has mushroom sauce.

📈 Future Improvements
Add semantic search using embeddings
Add recipe recommendations
Add user authentication
Add filtering and pagination
Deploy to cloud (Render / Railway / AWS)
Dockerize the application
🎯 Learning Outcomes
Through this project:

Integrated AI with relational databases
Implemented OpenAI Function Calling
Built a manual AI agent loop
Practiced SQLAlchemy ORM usage
Designed structured tool schemas
Connected AI to real backend services
📌 Why This Project Stands Out
Unlike traditional CRUD applications, this system allows conversational interaction with the database using AI.

It demonstrates:

Practical AI integration
Backend engineering skills
Database design
Understanding of AI agent architecture
