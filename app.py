from flask import Flask, render_template, request, send_from_directory, jsonify
import fitz
import os
import shutil
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/split', methods=['POST'])
def split_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    unique_filename = str(uuid.uuid4()) + ".pdf"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(file_path)

    x_coord = 200
    y_coord = 210
    width = 100
    height = 10
    created_files = extract_distinct_values_and_save_pdfs(file_path, x_coord, y_coord, width, height)

    os.remove(file_path)

    # Generate download and thumbnail links (assuming same for now)
    download_links = [f'/download/{filename}' for filename in created_files]
    thumbnail_links = download_links  # Assuming same links for thumbnails

    return jsonify({'message': 'PDF splitting completed!', 
                    'download_links': download_links,
                    'thumbnail_links': thumbnail_links}), 200

def extract_distinct_values_and_save_pdfs(pdf_path, x, y, width, height):
    extracted_values = {}
    doc = fitz.open(pdf_path)

    output_dir = os.path.join(app.config['UPLOAD_FOLDER'], "Extracted_PDFs")
    os.makedirs(output_dir, exist_ok=True)
    created_files = []

    for page_num in range(doc.page_count):
        page = doc[page_num]
        rect = fitz.Rect(x, y, x + width, y + height)
        text = page.get_text("text", clip=rect)

        if text:
            value = text.strip()
            if value not in extracted_values:
                extracted_values[value] = []
            extracted_values[value].append(page_num)

    for village_name, page_numbers in extracted_values.items():
        output_filename = f"{village_name}.pdf"
        output_pdf_path = os.path.join(output_dir, output_filename)
        new_doc = fitz.open()
        for page_num in page_numbers:
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        new_doc.save(output_pdf_path)
        created_files.append(output_filename)

    return created_files

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'] + "/Extracted_PDFs", filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True) 
