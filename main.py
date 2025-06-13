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
from datetime import date, datetime
import tempfile
import traceback

app = FastAPI(title="Dental Clinic API")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "")
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

def generate_openai_summary(prompt: str) -> str:
    try:
        client = openai.Client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are an expert data analyst."},{"role": "user", "content": prompt}],
            max_tokens=300
        )
        return response.choices[0].message.content #.strip()
    except Exception as e:
        print("❌ OpenAI API call failed:", e)
        return "Summary not available due to an error."

@app.get("/practitioners")
async def get_practitioners():
    try:
        with engine.begin() as conn:
            rows = conn.execute(text("SELECT full_name FROM practitioners ORDER BY full_name")).fetchall()
            return [r[0] for r in rows]
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/submit-appointment")
async def submit_appointment(request: Request):
    data = await request.json()
    try:
        with engine.begin() as conn:
            res = conn.execute(
                text("SELECT id FROM practitioners WHERE full_name = :name"),
                {"name": data.get("service")}
            ).fetchone()
            practitioner_id = res[0] if res else conn.execute(text("SELECT id FROM practitioners LIMIT 1")).fetchone()[0]

            conn.execute(text("""
                INSERT INTO appointments (patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id)
                VALUES (:name, :email, :date, :time, :service, :notes, :pid)
            """), {
                "name": data["name"],
                "email": data["email"],
                "date": data["date"],
                "time": data["time"],
                "service": data["service"],
                "notes": data.get("notes", ""),
                "pid": practitioner_id
            })

        return JSONResponse(status_code=201, content={"message": "Appointment created"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

@app.post("/upload-appointments")
async def upload_appointments(provider: str = Form(...), file: UploadFile = File(...)):
    try:
        # Save UploadFile to a real temp file (fix for SpooledTemporaryFile)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        df = pd.read_excel(tmp_path)

        with engine.begin() as conn:
            # Check if provider exists
            result = conn.execute(text("SELECT id FROM practitioners WHERE full_name = :name"), {"name": provider}).fetchone()
            if result:
                practitioner_id = result[0]
            else:
                res = conn.execute(text("INSERT INTO practitioners (full_name) VALUES (:name) RETURNING id"), {"name": provider})
                practitioner_id = res.scalar()

            added = 0
            for _, row in df.iterrows():
                # Basic validation
                if not row.get("Patient Name") or not row.get("Appointment Date") or not row.get("Appointment Time"):
                    continue

                # Check if same record exists
                exists = conn.execute(text("""
                    SELECT id FROM appointments
                    WHERE patient_name = :name
                      AND appointment_date = :date
                      AND appointment_time = :time
                      AND practitioner_id = :pid
                """), {
                    "name": row["Patient Name"],
                    "date": str(row["Appointment Date"]),
                    "time": str(row["Appointment Time"]),
                    "pid": practitioner_id
                }).fetchone()

                if not exists:
                    conn.execute(text("""
                        INSERT INTO appointments
                        (patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id)
                        VALUES (:name, :email, :date, :time, :service, :notes, :pid)
                    """), {
                        "name": row.get("Patient Name"),
                        "email": row.get("Patient Email"),
                        "date": str(row["Appointment Date"]),
                        "time": str(row["Appointment Time"]),
                        "service": row.get("Service"),
                        "notes": row.get("Notes"),
                        "pid": practitioner_id
                    })
                    added += 1

        return {"message": f"{added} appointments added for {provider}."}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

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
async def generate_report(background: BackgroundTasks, startDate: str = None, endDate: str = None, providers: list[str] = Query(default=[])):
    try:
        conditions = []
        params = {}

        if startDate and endDate:
            conditions.append("appointment_date BETWEEN :start AND :end")
            params.update({"start": startDate, "end": endDate})

        if providers:
            conditions.append("p.full_name = ANY(:providers)")
            params["providers"] = providers

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT a.patient_name, a.patient_email, a.appointment_date, a.appointment_time,
                   a.service, a.notes, p.full_name AS practitioner
            FROM appointments a
            JOIN practitioners p ON a.practitioner_id = p.id
            {where_clause}
            ORDER BY a.appointment_date, a.appointment_time
        """

        # ✅ DEBUG LOGGING
        #print("\n--- GENERATE REPORT ---")
        #print("QUERY:", query)
        #print("PARAMS:", params)

        # ✅ SAFE DB ACCESS
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)

        if df.empty:
            return JSONResponse(status_code=404, content={"error": "No data found for selected filters."})

        # Generate summary using OpenAI
        summary_prompt = f"Summarize this dental appointment report:\n\n{df.to_string(index=False)}"
        summary = generate_openai_summary(summary_prompt)

        # Prepare Word report based on uploaded template
        from docxtpl import DocxTemplate
        from docx.shared import Inches
        from docx.enum.section import WD_ORIENT
        from docx import Document
        import pypandoc

        template_path = "./report_template.docx"
        if not os.path.exists(template_path):
            return JSONResponse(status_code=500, content={"error": "Template not found."})

        doc = DocxTemplate(template_path)

        # Format today’s date according to locale
        date_str = datetime.now().strftime("%B %d, %Y")

        # Render table rows for Word template
        table_data = df.to_dict(orient="records")

        context = {
            "dateField": date_str,
            "summaryField": summary,
            "rawDataField": table_data,
        }

        doc.render(context)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_docx:
            doc.save(temp_docx.name)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as output_pdf:
            pypandoc.convert_file(temp_docx.name, "pdf", outputfile=output_pdf.name)

        # Schedule deletion
        background.add_task(cleanup_temp_files, temp_docx.name, output_pdf.name)

        return StreamingResponse(
            open(output_pdf.name, "rb"), 
            media_type="application/pdf", 
            headers={
                "Content-Disposition": "attachment; filename=appointment_report.pdf"
            },
            background=background
        )

    except Exception as e:
        print("\n⚠️ Exception in /generate-report:")
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
