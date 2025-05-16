
# Database requirement
- mySQL

# Backend Installation
### Make sure your on the backend directory on a seperate terminal
1. cd /backend
2. create a `.env` and follow the `.env.example`
3. Set up a virtual environment: `python -m venv venv`
4. Activate the environment:
    - Windows(git bash): `source venv/Scripts/activate`
    - Windows(cmd): `venv\Scripts\activate.bat`
    - Windows(powershell): `.\venv\Scripts\Activate.ps1`
    - Windows: `venv\Scripts\activate`
    - macOS/Linux: `source venv/bin/activate`
5. Install requirements `pip install -r requirements.txt`
6. Run development server `fastapi dev app.py --port 5000`
7. Can ignore these warnings and errors. 'Warning: Trigger does not exist
  await self._query(query)
⚠️  Skipped measurement 36 due to metric value error.
⚠️  Skipped measurement 41 due to metric value error.
⚠️  Skipped measurement 42 due to metric value error.'

# Frontend Installation
### Make sure your on the frontend directory on a seperate terminal
1. cd /frontend
2. npm install
3. npm run dev

# Solution Approach
1. Backend First:
   Started by reviewing sample_data.json, schema.md, and api.md to understand the data structure and API requirements.
2. Schema Design:
 - Designed the schema primarily based on the example API responses for accuracy.
 - Used ENUM types for fields like name and unit in the metrics table and quality in the climate_measurements table, since these values are static and predictable.
 - Limited the country field in the locations table to 28 characters, based on the length of the longest existing country name.
 - Identified an anomaly in the sample data related to metric values. Added a validation hook to reject out-of-range values based on the metric type.
3. Database Setup (db.py):
 - Centralized the database connection to avoid unnecessary connection pooling.
 - Added utility functions to create the schema, seed data, and drop tables for easy database initialization during app startup.
4. API Development:
 - Implemented endpoints as defined in api.md.
 - Supported dynamic filtering and safe date parsing.
 - Added pagination support to the climate endpoint, with default values (limit=200, offset=50).
 - Ensured date formats matched sample responses by stripping time info (ideally handled through Pydantic models).
5. Testing with Postman:
 - Created and ran test queries using `EcoVision API - Seed Data Tests.postman_collection.json` to validate endpoint behavior and ensure accurate responses.
6. Frontend:
 - Spent time analyzing how the frontend consumes API data before implementing features and how each component works.
7. API Integration (api.js):
 - Built this first as it was the easiest entry point for linking frontend to backend.
8. Filters Component (Filters.jsx):
 - Implemented based on the provided TODO list, validating functionality as I progressed.
9. Main App Component (App.jsx):
 - Refactored fetchData to use the new API endpoints.
 - Added useEffect to prevent unnecessary re-renders and optimize performance.
 - In hindsight, this should have been prioritized before Filters.jsx since it was easier to work with.
10. End-to-End Testing:
 - Manually verified if components and APIs worked together as expected.

# Tools Used/Frameworks
1. VSCode
 - Lightweight and extensible IDE that improves developer productivity through integrated tools and debugging support.
2. Pylance extension
 - Offers advanced type checking, code navigation, and autocompletion features for Python, streamlining development.
3. Eslint extension
 - Helps maintain consistent and clean JavaScript/React code by identifying issues in real-time.
4. Prettier extension
 - Automatically formats code for better readability and consistency across the codebase.
5. Fastapi
 - Chosen for its high performance and async capabilities.
 - Ideal for building well-structured RESTful APIs that handle high I/O workloads efficiently.
6. aiomysql(async mysql)
 - Enables non-blocking MySQL operations, allowing the backend to handle concurrent database queries efficiently. Suitable for real-time and high-load applications.
7. ChatGPT
 - Assisted with generating seed data, validating equations, and writing boilerplate code.
8. Postman
 - Used for testing and validating API endpoints, simulating various query scenarios, and ensuring responses matched expected output.
9. MySQL workbench
 - Used for visualizing and debugging the database schema, inspecting data integrity, and verifying relational mappings between tables.