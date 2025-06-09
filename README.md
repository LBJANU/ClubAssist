# ClubAssist - University of Michigan Club Interview Assistant

ClubAssist is a Django-based web application that helps students prepare for club interviews at the University of Michigan using AI assistance. This is probably going to be the greatest thing you ever see

## Features
- AI-powered interview preparation
- Club interview scheduling
- Practice questions and feedback
- Interview tips and resources

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with the following variables:
```
SECRET_KEY=your_django_secret_key
DEBUG=True
OPENAI_API_KEY=your_openai_api_key
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

Visit http://localhost:8000 to access the application.

## Project Structure
- `clubassist/` - Main Django project directory
- `interviews/` - App for managing interviews
- `users/` - App for user management
- `ai_assistant/` - App for AI integration

## Contributing
Please read our contributing guidelines before submitting pull requests.

## License
MIT License 
