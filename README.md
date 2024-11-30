# Real Estate Management System

A FastAPI-based real estate management system using HTMX for dynamic interactions and MySQL for data storage.

## Features

- **Property Management**
  - Add, edit, and delete property listings
  - Support for both residential and commercial properties
  - Image upload and management
  - Property status tracking

- **Agent Management**
  - Agent profiles and credentials
  - License tracking
  - Performance metrics
  - Sales tracking

- **User Authentication**
  - Role-based access control (Admin/Agent)
  - Secure password handling
  - Session management
  - Environmental admin support

- **Client Management**
  - Client profiles
  - Property viewings
  - Transaction history
  - Portfolio tracking

## Technology Stack

- **Backend**: FastAPI
- **Frontend**: HTMX, TailwindCSS
- **Database**: MySQL
- **Authentication**: Session-based with bcrypt
- **Templating**: Jinja2

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/real-estate-management.git
cd real-estate-management
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=real_estate
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_admin_password
SECRET_KEY=your_secret_key
ENVIRONMENT=development
```

5. Initialize the database:
```bash
python manage_db.py init
```

## Running the Application

1. Start the server:
```bash
uvicorn app.main:app --reload
```

2. Access the application at `http://localhost:8000`

## Project Structure

```
.
├── app/
│   ├── core/
│   │   ├── config.py      # Configuration settings
│   │   ├── database.py    # Database connection handling
│   │   ├── security.py    # Authentication and security
│   │   └── logging_config.py  # Logging configuration
│   ├── routes/
│   │   ├── admin.py       # Admin routes
│   │   ├── agents.py      # Agent routes
│   │   ├── auth.py        # Authentication routes
│   │   └── main.py        # Main routes
│   ├── sql/
│   │   ├── schema.sql     # Database schema
│   │   └── procedures.sql # Stored procedures
│   ├── static/
│   │   └── css/          # CSS files
│   └── templates/        # HTML templates
└── manage_db.py         # Database management script
```

## Database Management

- Initialize database: `python manage_db.py init`
- Reset database: `python manage_db.py reset`

## Security Features

- Password hashing using bcrypt
- Session-based authentication
- Role-based access control
- Secure password storage
- CSRF protection
- SQL injection prevention through stored procedures

## Stored Procedures

The system uses stored procedures for all database operations to ensure:
- Data consistency
- Security
- Performance optimization
- Business logic encapsulation

Key procedures include:
- User authentication
- Property management
- Agent operations
- Client management
- Transaction handling

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Authors

- Tyler Gilman, Nick Mascolo, George Megdanis

## Acknowledgments

- FastAPI documentation
- HTMX documentation
- MySQL documentation
