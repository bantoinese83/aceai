# AceAI

AceAI is a web application designed to help users ace their interviews with the assistance of AI. It provides features such as speech recognition, audio recording, and real-time feedback on interview answers.

## Features

- **Speech Recognition**: Uses webkitSpeechRecognition to transcribe spoken words into text.
- **Audio Recording**: Records audio responses and evaluates them.
- **Real-Time Feedback**: Provides feedback on filler words and overall performance.
- **Interview Simulation**: Simulates interview questions and records user responses.
- **Review and Advice**: Offers review and advice based on the user's answers.

## Technologies Used

- **Python**: Backend logic and API endpoints.
- **Flask**: Web framework for handling HTTP requests and rendering templates.
- **JavaScript**: Frontend logic for handling speech recognition and audio recording.
- **HTML/CSS**: Markup and styling for the web pages.
- **SQLAlchemy**: ORM for database interactions.
- **Amazon Polly**: Text-to-speech service for generating interview questions.
- **Google Generative AI**: For generating interview questions and evaluating answers.

## Installation

1. **Clone the repository**:
    ```sh
    git clone https://github.com/bantoinese83/aceai.git
    cd aceai
    ```

2. **Create a virtual environment**:
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

4. **Set up environment variables**:
    - Create a `.env` file in the root directory.
    - Add the following variables:
        ```plaintext
        FLASK_SECRET_KEY=your_secret_key
        DATABASE_URL=your_database_url
        GEMINI_API_KEY=your_gemini_api_key
        AWS_ACCESS_KEY_ID=your_aws_access_key_id
        AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
        ```

5. **Initialize the database**:
    ```sh
    flask db upgrade
    ```

6. **Run the application**:
    ```sh
    flask run
    ```

## Usage

1. **Navigate to the home page**: Open your browser and go to `http://127.0.0.1:5000/`.
2. **Start an interview**: Fill in your details and start the interview.
3. **Record your answers**: Use the provided buttons to start and stop recording.
4. **Get feedback**: Review the transcription, score, and advice provided by the AI.

## Contributing

1. **Fork the repository**.
2. **Create a new branch**:
    ```sh
    git checkout -b feature/your-feature-name
    ```
3. **Commit your changes**:
    ```sh
    git commit -m 'Add some feature'
    ```
4. **Push to the branch**:
    ```sh
    git push origin feature/your-feature-name
    ```
5. **Open a pull request**.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Flask](https://flask.palletsprojects.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Amazon Polly](https://aws.amazon.com/polly/)
- [Google Generative AI](https://cloud.google.com/ai-platform/)

## Contact

For any inquiries, please contact [your-email@example.com].