Setup steps

1. Open this folder in VS Code.
2. Open a terminal in VS Code (Ctrl + backtick).
3. Create and activate the virtual environment:
   python -m venv venv
   venv\Scripts\activate
4. Install the Python packages:
   pip install -r requirements.txt
5. Set up the React frontend (this folder is not included, create it fresh):
   npm create vite@latest frontend -- --template react
   Then copy frontend/src/App.jsx from this project into the new frontend/src/App.jsx, overwriting it.
6. Install frontend packages and build it:
   cd frontend
   npm install
   npm run build
   cd ..
7. Run the app:
   python main.py

Note: the frontend folder here only contains src/App.jsx, since the rest of a Vite project
(package.json, index.html, config files, node_modules) needs to be generated fresh by the
npm create vite command on your machine.
