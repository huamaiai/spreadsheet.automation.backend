# Dental Clinic FastAPI Backend

## Setup

1. Create a virtual environment:

    ```bash
    python -m venv env
    source env/bin/activate  # or env\Scripts\activate on Windows
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Set up database (PostgreSQL or MySQL):

    - Use `dental_clinic_postgres.sql` or `dental_clinic_mysql.sql`

4. Run the app:

    ```bash
    uvicorn main:app --reload
    ```

## Environment Variables

Create a `.env` file or set the following:

- `OPENAI_API_KEY=your-api-key-here`
- `DATABASE_URL=postgresql://user:pass@localhost/dbname`

## PDF Report Requirements

This project uses `docxtpl` to load `.dotx` templates and `pypandoc` to convert `.docx` to PDF.

### On Linux

```bash
sudo apt-get install pandoc libreoffice
```

### On Windows

- [Install Pandoc](https://pandoc.org/installing.html)
- [Install LibreOffice](https://www.libreoffice.org/download/download/)
- If using Word, ensure it's set as default app for .docx

`pypandoc` will try multiple fallback methods to generate PDF.
