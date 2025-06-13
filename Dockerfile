FROM python:3.11-slim

# Install dependencies for PDF generation
RUN apt-get update && \
    apt-get install -y pandoc libreoffice && \
    apt-get clean
RUN apt-get update && apt-get install -y pandoc texlive texlive-xetex texlive-latex-extra

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
