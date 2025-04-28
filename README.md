# InhaGianHub

## Table of Contents

-   [Getting Started](#getting-started)
-   [LICENSE](#license)

---

## Getting Started

### 1. Set Up Environment Variables

Create a `.env` file or set the following parameters for database connection:

```env
# .env example
MYSQL_ROOT_PASSWORD=your_root_password
MYSQL_DATABASE=your_database_name
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
DB_HOST=db
DB_PORT=3306
```

### 2. Run with Docker (Recommended)

If you have Docker and Docker Compose installed, you can easily start the project:

```bash
docker-compose up --build
```

This will set up both the FastAPI server and the MySQL database in containers.

Access FastAPI: http://localhost:8000

MySQL runs on port 3306 inside the container.

To stop the containers:

```bash
docker-compose down
```

### 3. Run Locally (Without Docker)

If you prefer running locally:

Make sure MySQL is running with the above environment settings.

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

---

## LICENSE

This project is licensed under the Apache License 2.0.

You may use, modify, and distribute this software in compliance with the License.
It also provides an explicit grant of patent rights from contributors.

See the [LICENSE](./LICENSE) file for detailed information.
