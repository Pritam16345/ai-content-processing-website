# CogniCore AI: Your Personal Knowledge Base


CogniCore is a full-stack web application that transforms unstructured content from YouTube videos, websites, and PDFs into a personal, interactive knowledge base. Users can process any source, and then have an intelligent conversation with their documents, asking specific questions and receiving AI-generated answers based on the content.

## ✨ Key Features

* **Multi-Source Ingestion:** Process and extract content from various sources:
    * **YouTube Videos:** Automatically transcribes video audio to text.
    * **Web Articles:** Scrapes and cleans the main content from any URL.
    * **PDF Documents:** Extracts all text from uploaded PDF files.
* **User Authentication:** Secure user registration and login system to keep each user's knowledge base private.
* **AI-Powered Chat:** Engage in a conversation with your documents. The application uses a Retrieval-Augmented Generation (RAG) pipeline to provide accurate answers.
* **Persistent Knowledge Base:** All processed sources are saved to a user-specific database, allowing you to build and query your knowledge library over time.
* **Sleek Frontend:** A modern and responsive user interface built with vanilla JavaScript, HTML, and CSS for a fast and intuitive experience.

## 🛠️ Technology Stack

This project is a full-stack application built with a modern, AI-centric architecture.

* **Backend:**
    * **Framework:** FastAPI
    * **Database:** SQLAlchemy with SQLite
    * **AI & ML:**
        * **Transcription:** OpenAI Whisper
        * **Embeddings:** Sentence-Transformers (`all-MiniLM-L6-v2`)
        * **Vector Store:** FAISS for efficient similarity search
        * **Text Splitting:** LangChain (`RecursiveCharacterTextSplitter`)
        * **Generative AI:** Cloudflare Workers AI (for LLM inference)
    * **Data Extraction:** `yt-dlp` (YouTube), `trafilatura` (Websites), `PyMuPDF` (PDFs)
    * **Authentication:** Passlib for password hashing

* **Frontend:**
    * **Languages:** HTML5, CSS3, JavaScript (ES6+)
    * **No Frameworks:** Built with vanilla JS for a lightweight and fast user experience.

* **Infrastructure:**
    * **API Communication:** RESTful API
    * **CORS:** Handled with FastAPI Middleware

## 🚀 Getting Started

Follow these instructions to set up and run the project locally.

### Prerequisites

* Python 3.9+
* Node.js (for frontend, if you plan to add a package manager)
* `ffmpeg` installed and available in your system's PATH.

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YourUsername/Your-Repository-Name.git](https://github.com/YourUsername/Your-Repository-Name.git)
    cd Your-Repository-Name/ai_content_processor
    ```

2.  **Set up the Python backend:**
    ```bash
    # Create and activate a virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`

    # Install dependencies
    pip install -r requirements.txt
    ```

3.  **Run the backend server:**
    ```bash
    uvicorn main:app --reload
    ```
    The backend API will now be running at `http://127.0.0.1:8000`.

4.  **Launch the frontend:**
    * Navigate to the `ai_content_frontend` directory.
    * Open the `index.html` file directly in your web browser.

You can now register a new user and start processing content!
