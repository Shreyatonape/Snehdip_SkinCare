# Snehdip SkinCare Hospital

A comprehensive Flask-based web application for skin disease detection, appointment booking, and healthcare management system.

## Features

- 🏥 **Skin Disease Detection** - AI-powered skin disease classification using TensorFlow
- 👨‍⚕️ **Doctor-Patient Management** - Complete appointment booking system
- 📧 **Email Notifications** - Automated appointment confirmations
- 💬 **AI Chatbot** - Medical assistance chatbot
- 🌐 **Multi-language Support** - English, Hindi, Marathi
- 🔐 **User Authentication** - Secure login/registration system
- 📊 **Dashboard** - Patient and doctor dashboards

## Tech Stack

- **Backend**: Flask, SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **AI/ML**: TensorFlow, Keras
- **Database**: PostgreSQL
- **Email**: Flask-Mail with Gmail SMTP
- **Real-time**: Socket.IO

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Gmail account (for email notifications)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd Snehdip-SkinCare
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   - Copy `.env.example` to `.env`
   - Update with your credentials:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/skincare_db
   SECRET_KEY=your-secret-key
   GEMINI_API_KEY=your-gemini-api-key
   MAIL_USERNAME=your-gmail@gmail.com
   MAIL_PASSWORD=your-gmail-app-password
   ```

5. **Database Setup**
   ```bash
   # Create database
   createdb skincare_db
   
   # Initialize database
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

## Gmail App Password Setup

1. Enable 2-factor authentication on your Gmail account
2. Go to Google Account settings → Security → App Passwords
3. Generate a new app password for your application
4. Use this password in `MAIL_PASSWORD` (not your regular Gmail password)

## Project Structure

```
Skincare/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── extensions.py          # Flask extensions
├── utils/
│   └── translator.py     # Multi-language support
├── templates/            # HTML templates
├── static/              # CSS, JS, images
├── ml/                  # Machine learning models
├── requirements.txt      # Python dependencies
├── .env                # Environment variables
└── .gitignore          # Git ignore file
```

## API Endpoints

### User Management
- `POST /register` - User registration
- `POST /login` - User login
- `GET /logout` - User logout

### Appointments
- `POST /contact` - Book appointment
- `GET /doctor/appointments` - View appointments

### AI Features
- `POST /api/predict` - Skin disease prediction
- `POST /api/chatbot/ask` - AI chatbot

## Deployment

### Heroku Deployment
1. Create Heroku app
2. Set environment variables in Heroku dashboard
3. Push to Heroku:
   ```bash
   git push heroku main
   ```

### Vercel/Render
1. Connect repository to platform
2. Set environment variables
3. Deploy automatically

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Flask secret key |
| `GEMINI_API_KEY` | Gemini AI API key |
| `MAIL_USERNAME` | Gmail address for notifications |
| `MAIL_PASSWORD` | Gmail app password |

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Submit pull request

## License

This project is licensed under the MIT License.

## Support

For support and queries, contact:
- Email: supriyaawatade1205@gmail.com
- GitHub Issues: [Create Issue](link-to-issues)

## Acknowledgments

- TensorFlow for ML capabilities
- Flask framework
- Bootstrap for UI components
- Gemini AI for chatbot functionality
