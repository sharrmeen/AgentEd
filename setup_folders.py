import os


folders = [
    "backend/app/api",
    "backend/app/agents",
    "backend/app/services",
    "backend/app/models",
    "backend/app/db",
    "backend/app/utils",
    "backend/tests",
    "data/syllabus",
    "data/notes",
    "data/embeddings",
    "data/quiz_bank"
]


files = [
    "backend/main.py",
    "backend/requirements.txt",
    ".gitignore",
    "README.md"
]


for folder in folders:
    os.makedirs(folder, exist_ok=True)


for file in files:
    with open(file, "w") as f:
        pass

print("AgentEd project structure created successfully!")
