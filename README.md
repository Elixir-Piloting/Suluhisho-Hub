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

## Project Structure

### Core Components

1. **Authentication System** (`app/routes/auth.py`, `app/forms/auth.py`)
   - User registration and login
   - Email verification system
   - Password management and recovery
   - Session handling

2. **Post Management** (`app/models/post.py`, `app/routes/posts.py`)
   ```python
   ALLOWED_CATEGORIES = [
       'Infrastructure', 'Security', 'Environment',
       'Public Services', 'Transportation', 'Education',
       'Healthcare', 'Other'
   ]
   ```
   - Issue creation and tracking
   - Image upload handling
   - Geolocation integration
   - Category management

3. **Community Features**
   - Comment system with moderation
   - Solution suggestions
   - Upvoting mechanism
   - User reputation tracking

4. **Admin Dashboard** (`app/routes/admin.py`)
   - User management interface
   - Content moderation tools
   - System settings configuration
   - Analytics and reporting
   - Visual data representation using Chart.js
     - Posts by category distribution
     - Activity trends over time
   - Report generation with filters
     - Date range selection
     - Category filtering
     - Status filtering
     - Email report sharing

### Database Schema

1. **Users Collection**
   ```javascript
   {
       "_id": ObjectId,
       "username": String,
       "email": String,
       "password_hash": String,
       "role": String,
       "profile_picture": String,
       "created_at": DateTime,
       "last_login": DateTime
   }
   ```

2. **Posts Collection**
   ```javascript
   {
       "_id": ObjectId,
       "title": String,
       "description": String,
       "author_id": ObjectId,
       "category": String,
       "location": {
           "type": "Point",
           "coordinates": [Number, Number]
       },
       "images": Array,
       "status": String,
       "upvotes": Array,
       "created_at": DateTime
   }
   ```

### Frontend Implementation

1. **Base Template** (`templates/base.html`)
   - Responsive navigation system
   - User menu integration
   - Real-time notification display
   - Mobile-friendly design

2. **JavaScript Features** (`static/js/main.js`)
   - Mobile menu toggle
   - Flash message handling
   - Form validation
   - Image preview
   - AJAX request management
   - Map interaction

### Security Features

1. **Authentication**
   - Password hashing using Werkzeug
   - Session management
   - CSRF protection
   - Rate limiting

2. **Data Protection**
   - Input sanitization
   - MongoDB injection prevention
   - XSS protection
   - Secure file uploads

### Map Integration

1. **Features**
   - Interactive issue mapping
   - Location-based clustering
   - Distance calculations
   - Area statistics

2. **Data Structure**
   ```javascript
   {
       "type": "Feature",
       "geometry": {
           "type": "Point",
           "coordinates": [longitude, latitude]
       },
       "properties": {
           "title": "Issue Title",
           "category": "Category",
           "status": "Status"
       }
   }
   ```

### Error Handling

1. **Custom Error Pages**
   - 404 Not Found
   - 403 Forbidden
   - 500 Server Error

2. **Error Logging**
   ```python
   @app.errorhandler(500)
   def internal_error(error):
       db.session.rollback()
       return render_template('errors/500.html'), 500
   ```

## Performance Optimizations

1. **Database**
   - Indexed collections
   - Optimized queries
   - Pagination implementation

2. **Frontend**
   - Lazy loading
   - Image optimization
   - Minified assets

## Dependencies

```
Flask==3.0.2
Flask-Login==0.6.3
Flask-Mail==0.9.1
Flask-WTF==1.2.1
pymongo==4.6.2
python-dotenv==1.0.1
bcrypt==4.1.2
email-validator==2.1.1
python-slugify==8.0.4
WTForms==3.1.2
geopy==2.4.1
Pillow==11.1.0
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with detailed description


## License



This project is licensed under the MIT License. 

©️ 2025 Suluhisho Hub. All rights reserved( Nzioka Stephen Mwaka ).