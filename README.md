# FitGenie AI Backend - FastAPI Server

This is the backend for **FitGenie AI**, an AI-powered fitness and diet recommendation application. It uses **FastAPI** and **Google Gemini AI** to process user input and generate personalized recommendations for diet and workout plans.

## Features

- **Personalized Recommendations**: Accepts user input via API and generates tailored fitness and diet plans.
- **Google Gemini Integration**: Uses **Google Gemini** to analyze user profiles and provide custom recommendations.
- **FastAPI Backend**: Provides a fast and efficient server to handle user requests.

## Setup

### Prerequisites

- Python 3.7 or higher
- `pip` for installing dependencies
- Google Gemini API key (must be configured in a `.env` file)

### Installation Steps

1. **Clone the repository**:

   ```bash
   git clone https://github.com/Shahzad-Ali-44/fitgenie-ai-backend.git
   
   cd fitgenie-ai-backend
   ```

2. **Set up environment variables**:

   Create a `.env` file in the project root directory and add your Google Gemini API key.

   ```env
   GOOGLE_API_KEY=your_google_api_key
   ```

3. **Install dependencies**:

   Install the required Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the FastAPI server**:

   Run the server with `uvicorn`:

   ```bash
   uvicorn main:app --reload
   ```


## License

This project is licensed under the [MIT License](LICENSE).

