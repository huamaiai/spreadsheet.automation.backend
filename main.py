from fastapi import FastAPI, Request, Query, BackgroundTasks, Form, File, UploadFile
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from docxtpl import DocxTemplate
import pandas as pd
import pypandoc
from io import BytesIO
import openai
import os
from babel.dates import format_date
from datetime import date
import tempfile

app = FastAPI(title="Dental Clinic API")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dental_clinic.db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
engine = create_engine(DATABASE_URL)
openai.api_key = OPENAI_API_KEY

def cleanup_temp_files(*paths):
    for path in paths:
        try:
            os.remove(path)
        except Exception:
            pass

def get_filtered_data(start_date=None, end_date=None, providers=None):
    filters = []
    params = {}

    if start_date and end_date:
        filters.append("appointment_date BETWEEN :start AND :end")
        params["start"] = start_date
        params["end"] = end_date

    if providers:
        provider_placeholders = ','.join(f":p{i}" for i in range(len(providers)))
        filters.append(f"pr.full_name IN ({provider_placeholders})")
        params.update({f"p{i}": name for i, name in enumerate(providers)})

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    query = text(f"""
        SELECT 
            ap.patient_name, ap.patient_email,
            ap.appointment_date, ap.appointment_time,
            ap.service, ap.notes,
            pr.full_name AS practitioner
        FROM appointments ap
        JOIN practitioners pr ON ap.practitioner_id = pr.id
        {where_clause}
        ORDER BY ap.appointment_date, ap.appointment_time
    """)

    with engine.begin() as conn:
        result = conn.execute(query, params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        return df

@app.get("/practitioners")
async def get_practitioners():
    try:
        with engine.begin() as conn:
            rows = conn.execute(text("SELECT full_name FROM practitioners ORDER BY full_name")).fetchall()
            return [r[0] for r in rows]
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/submit-appointment")
async def submit_appointment(data: dict):
    try:
        with engine.begin() as conn:
            res = conn.execute(text("SELECT id FROM practitioners WHERE full_name = :name"), {"name": data.get("service")}).fetchone()
            practitioner_id = res[0] if res else conn.execute(text("SELECT id FROM practitioners LIMIT 1")).fetchone()[0]

            conn.execute(text("""
                INSERT INTO appointments (patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id)
                VALUES (:name, :email, :date, :time, :service, :notes, :pid)
            """), {
                "name": data["name"], "email": data["email"], "date": data["date"], "time": data["time"],
                "service": data["service"], "notes": data.get("notes", ""), "pid": practitioner_id
            })
        return JSONResponse(status_code=201, content={"message": "Appointment created"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

@app.post("/upload-appointments")
async def upload_appointments(provider: str = Form(...), file: UploadFile = File(...)):
    try:
        df = pd.read_excel(file.file)
        with engine.begin() as conn:
            res = conn.execute(text("SELECT id FROM practitioners WHERE full_name = :name"), {"name": provider}).fetchone()
            practitioner_id = res[0] if res else conn.execute(text("INSERT INTO practitioners (full_name) VALUES (:name) RETURNING id"), {"name": provider}).scalar()

            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO appointments (patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id)
                    VALUES (:pn, :pe, :ad, :at, :s, :n, :pid)
                """), {
                    "pn": row['patient_name'], "pe": row['patient_email'], "ad": row['appointment_date'],
                    "at": row['appointment_time'], "s": row['service'], "n": row.get('notes', ''), "pid": practitioner_id
                })
        return {"message": "Upload successful"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

@app.get("/export-excel")
def export_excel(
    startDate: str = Query(None),
    endDate: str = Query(None),
    providers: list[str] = Query(None)
):
    df = get_filtered_data(startDate, endDate, providers)
    if df.empty:
        return JSONResponse(status_code=404, content={"error": "No data found"})

    # Generate Excel in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Appointments")
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=appointments.xlsx"}
    )

@app.get("/generate-report")
async def generate_report(request: Request, background_tasks: BackgroundTasks, startDate: str = None, endDate: str = None, providers: list[str] = Query(default=[])):
    try:
        # Extract Accept-Language
        accept_language = request.headers.get("accept-language", "en")
        locale_code = accept_language.split(",")[0]

        # Query data
        query = """
            SELECT a.patient_name, a.patient_email, a.appointment_date, a.appointment_time,
                   a.service, a.notes, p.full_name AS practitioner
            FROM appointments a
            JOIN practitioners p ON a.practitioner_id = p.id
            WHERE 1=1
        """
        params = {}
        if startDate and endDate:
            query += " AND appointment_date BETWEEN :start AND :end"
            params.update({"start": startDate, "end": endDate})
        if providers:
            query += " AND p.full_name IN :providers"
            params.update({"providers": tuple(providers)})

        with engine.begin() as conn:
            df = pd.read_sql(text(query), conn, params=params)

        if df.empty:
            return JSONResponse(status_code=404, content={"message": "No data found"})

        # Generate summary
        prompt = f"Summarize the following dental appointment data: {df.to_markdown(index=False)}"
        summary = "No summary generated."
        if OPENAI_API_KEY:
            client = openai.Client()
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "You are an expert data analyst."},{"role": "user", "content": prompt}],
                max_tokens=300
            )
            summary = response.choices[0].message.content #.strip()

        # Format date with locale
        locale_code = locale_code.replace("-", "_")
        today = format_date(date.today(), locale=locale_code)

        # Load and populate Word template
        template_path = "./report_template.docx"
        doc = DocxTemplate(template_path)

        # Convert dataframe to list of dicts for docxtpl
        table_data = df.to_dict(orient="records")
        doc.render({
            "dateField": today,
            "summaryField": summary,
            "rawDataField": table_data
        })

        # Save to temporary docx file
        temp_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        doc.save(temp_docx.name)

        # Convert to PDF using pypandoc
        output_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pypandoc.convert_file(temp_docx.name, "pdf", outputfile=output_pdf.name)
        
        background_tasks.add_task(cleanup_temp_files, temp_docx.name, output_pdf.name)

        # Stream back PDF
        return StreamingResponse(
            open(output_pdf.name, "rb"),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=clinic_report.pdf"}
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
