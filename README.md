# Suluhisho Hub

Suluhisho Hub is a community-driven platform where users can post, discuss, and resolve local issues. The platform enables community members to collaborate on identifying and solving problems in their area.

## Features

- User Authentication (signup, login, email verification)
- Post Creation and Management
- Interactive Map Integration
- Community Interactions (comments, suggestions, upvotes)
- User Profiles and Account Management
- Admin and Moderator Tools
- Real-time Notifications
- Custom Error Pages

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: MongoDB
- **Frontend**: HTML, CSS, JavaScript
- **Mapping**: Leaflet.js with OpenStreetMap
- **Templating**: Jinja2
- **Authentication**: Flask-Login, Flask-Mail
- **Image Handling**: Flask-Uploads

## Setup Instructions

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with the following variables:
   ```
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=your_secret_key
   MONGODB_URI=your_mongodb_uri
   MAIL_SERVER=your_mail_server
   MAIL_PORT=your_mail_port
   MAIL_USERNAME=your_mail_username
   MAIL_PASSWORD=your_mail_password
   MAIL_USE_TLS=True
   ```
5. Initialize the database:
   ```bash
   flask init-db
   ```
6. Run the application:
   ```bash
   flask run
   ```

## Project Structure

```
suluhisho_hub/
├── app/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── templates/
│   ├── models/
│   ├── routes/
│   └── utils/
├── instance/
├── tests/
├── venv/
├── .env
├── .gitignore
├── requirements.txt
├── run.py
└── README.md
```

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License. 