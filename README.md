# AutoDoc AI 📄

AutoDoc AI is a full-stack application designed to automate the creation of professional documents. By leveraging Google's Gemini AI and Supabase, it allows users to generate structured Word documents and PowerPoint presentations from simple text prompts.

## Repository Structure

This project uses a monorepo-like structure within a single repository, linking directly to the respective source directories:

* **[Backend Repo (FastAPI/Python)](https://github.com/devrihan/backend-ocean)**: Contains the core API for AI generation, document processing, and database routing.
* **[Frontend Repo (React/TypeScript)](https://github.com/devrihan/ocean-front)**: Contains the user interface built with React, Vite, and Tailwind CSS.

## Features

* **AI Content Generation**: Uses Google Gemini to create outlines, draft content, and refine text.
* **Smart Outline Management**:
    * **AI Suggest**: Automatically generate structured outlines based on your topic.
    * **Customizable Structure**: Easily add, edit, or delete outline sections to fit your needs before generating full content.
* **Dual Format Export**:
    * **Word (.docx)**: Generates formatted reports with headings and paragraphs.
    * **PowerPoint (.pptx)**: Creates slide decks with bullet points, utilizing custom templates (Basic, Geometric, Scientific, Product).
* **Smart Editor**:
    * **AI Refinement**: Rewrite sections to be more formal, concise, or detailed.
    * **Image Integration**: Upload and attach images to specific document sections.
    * **Feedback Loop**: Like, dislike, and comment on generated sections.
* **Project Dashboard**: Manage multiple document projects with a user-friendly interface.
* **Secure Auth**: Full user authentication and profile management via Supabase.

## Tech Stack

### Frontend
* **Framework**: React 18 (Vite)
* **Language**: TypeScript
* **Styling**: Tailwind CSS, Shadcn UI

### Backend
* **Framework**: FastAPI (Python)
* **AI Model**: Google Gemini (`google-generativeai`)
* **Document Processing**: `python-docx`, `python-pptx`

### Infrastructure
* **Database**: PostgreSQL (Supabase)
* **Storage**: Supabase Storage (Bucket: `project_assets`)
* **Authentication**: Supabase Auth

## Prerequisites

* **Node.js** (v18 or higher)
* **Python** (v3.9 or higher)
* A **Supabase** account and project.
* A **Google Cloud** project with the Gemini API enabled.

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/devrihan/autodoc-ai.git
cd autodoc-ai
```

### 2. Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create and activate a virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the `backend` folder and add the following keys:

```env
# Supabase Configuration (Found in Project Settings -> API)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Auth Configuration (Found in Project Settings -> API -> JWT Settings)
JWT_SECRET=your_supabase_jwt_secret

# Google Gemini AI
GEMINI_API_KEY=your_google_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
```

Start the backend server:

```bash
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

Open a new terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
# or
bun install
```

Create a `.env` file in the `frontend` folder:

```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_PUBLISHABLE_KEY=your_supabase_anon_key
VITE_API_URL=http://localhost:8000
```

Start the development server:

```bash
npm run dev
```

## Database Setup (Supabase)

To make the application work, you need to set up the database schema and storage in Supabase.

1.  **Database Tables**: Go to the **SQL Editor** in your Supabase dashboard and run the SQL migrations found in `frontend/supabase/migrations/`. This will create the following tables:
    * `profiles`
    * `projects`
    * `sections`
    * `refinements`
    * `feedback`

2.  **Storage**:
    * Go to the **Storage** section in Supabase.
    * Create a new public bucket named `project_assets`.
    * Add a storage policy to allow authenticated users to insert (upload) and select (view) files.

## Usage

1.  **Access the App**: Open your browser and navigate to `http://localhost:8080` (or the port shown in your terminal).
2.  **Sign Up**: Create an account to access the dashboard.
3.  **Create a Project**:
    * Click "New Project".
    * Enter a **Title** and a **Topic** (e.g., "The Impact of AI on Healthcare").
    * Choose **Word** or **PowerPoint**.
    * Click **AI Suggest** to generate an outline, then **Create & Generate**.
4.  **Edit & Export**:
    * Use the editor to view the generated content.
    * Use the "Refine" input to ask AI to rewrite specific sections.
    * Upload images to sections.
    * Click **Export** to download the final `.docx` or `.pptx` file.

