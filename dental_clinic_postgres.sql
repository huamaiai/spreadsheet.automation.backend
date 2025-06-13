-- PostgreSQL schema with CASCADE
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS practitioners;

CREATE TABLE practitioners (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255)
);

CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    patient_name VARCHAR(255) NOT NULL,
    patient_email VARCHAR(255),
    appointment_date DATE,
    appointment_time TIME,
    service VARCHAR(255),
    notes TEXT,
    practitioner_id INTEGER REFERENCES practitioners(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO practitioners (id, full_name, email) VALUES (1, 'Dr. Alice Johnson', 'alice@example.com');
INSERT INTO practitioners (id, full_name, email) VALUES (2, 'Dr. Bob Smith', 'bob@example.com');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (1, 'Patient 1 A', 'pa1@example.com', '2025-06-12', '9:00:00', 'Checkup', 'Note 1', 1, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (2, 'Patient 2 A', 'pa2@example.com', '2025-06-13', '10:00:00', 'Teeth Cleaning', 'Note 2', 1, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (3, 'Patient 3 A', 'pa3@example.com', '2025-06-14', '11:00:00', 'Checkup', 'Note 3', 1, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (4, 'Patient 4 A', 'pa4@example.com', '2025-06-15', '12:00:00', 'Checkup', 'Note 4', 1, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (5, 'Patient 5 A', 'pa5@example.com', '2025-06-16', '13:00:00', 'Checkup', 'Note 5', 1, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (6, 'Patient 6 A', 'pa6@example.com', '2025-06-17', '9:00:00', 'Extraction', 'Note 6', 1, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (7, 'Patient 7 A', 'pa7@example.com', '2025-06-18', '10:00:00', 'Filling', 'Note 7', 1, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (8, 'Patient 8 A', 'pa8@example.com', '2025-06-19', '11:00:00', 'Braces', 'Note 8', 1, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (9, 'Patient 9 A', 'pa9@example.com', '2025-06-20', '12:00:00', 'Implant', 'Note 9', 1, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (10, 'Patient 10 A', 'pa10@example.com', '2025-06-21', '13:00:00', 'Whitening', 'Note 10', 1, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (11, 'Patient 1 B', 'pb1@example.com', '2025-06-12', '10:30:00', 'Implant', 'Note 1', 2, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (12, 'Patient 2 B', 'pb2@example.com', '2025-06-13', '11:30:00', 'Braces', 'Note 2', 2, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (13, 'Patient 3 B', 'pb3@example.com', '2025-06-14', '12:30:00', 'Extraction', 'Note 3', 2, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (14, 'Patient 4 B', 'pb4@example.com', '2025-06-15', '13:30:00', 'Whitening', 'Note 4', 2, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (15, 'Patient 5 B', 'pb5@example.com', '2025-06-16', '10:30:00', 'Braces', 'Note 5', 2, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (16, 'Patient 6 B', 'pb6@example.com', '2025-06-17', '11:30:00', 'Teeth Cleaning', 'Note 6', 2, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (17, 'Patient 7 B', 'pb7@example.com', '2025-06-18', '12:30:00', 'Filling', 'Note 7', 2, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (18, 'Patient 8 B', 'pb8@example.com', '2025-06-19', '13:30:00', 'Root Canal', 'Note 8', 2, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (19, 'Patient 9 B', 'pb9@example.com', '2025-06-20', '10:30:00', 'Whitening', 'Note 9', 2, '2025-06-12 12:46:23');
INSERT INTO appointments (id, patient_name, patient_email, appointment_date, appointment_time, service, notes, practitioner_id, created_at) VALUES (20, 'Patient 10 B', 'pb10@example.com', '2025-06-21', '11:30:00', 'Teeth Cleaning', 'Note 10', 2, '2025-06-12 12:46:23');


-- Adjust sequence for appointments table
SELECT setval('appointments_id_seq', (SELECT MAX(id) FROM appointments));

-- Do the same for practitioners if needed:
SELECT setval('practitioners_id_seq', (SELECT MAX(id) FROM practitioners));
