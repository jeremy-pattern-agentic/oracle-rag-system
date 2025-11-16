I’ll outline how to build a Retrieval-Augmented Generation (RAG) system in Python that can ingest various document types (PDF, DOCX, etc.), addressing document parsing, OCR for scanned PDFs, table extraction, and maintaining a high success rate with new formats. I’ll provide a clear, structured approach with code examples, focusing on practical implementation while keeping it concise yet comprehensive.

### Overview of the RAG System
A RAG system combines document retrieval and text generation. It ingests documents, extracts text (and optionally tables), stores embeddings in a vector database, retrieves relevant chunks based on queries, and generates responses using a language model. The system needs to handle diverse document formats, including PDFs (text and scanned) and DOCX, while ensuring robustness for new formats.

### System Architecture
1. **Document Ingestion**:
   - Parse PDFs (text and scanned) and DOCX files.
   - Use OCR for scanned PDFs.
   - Extract tables from PDFs.
2. **Text Processing**:
   - Clean and chunk extracted text.
   - Store embeddings in a vector database (e.g., FAISS, Chroma).
3. **Retrieval**:
   - Query the vector database to retrieve relevant document chunks.
4. **Generation**:
   - Pass retrieved chunks to a language model (e.g., via Hugging Face or an API like xAI’s Grok API).
5. **Error Handling and Format Adaptability**:
   - Implement fallback mechanisms and logging to maintain a 96%+ success rate.

### Step-by-Step Implementation

#### 1. Document Ingestion
We’ll use the following libraries:
- **PyPDF2** and **pdfplumber** for PDF text extraction (pdfplumber is better for tables).
- **python-docx** for DOCX files.
- **pytesseract** with **Tesseract OCR** for scanned PDFs.
- **pandas** for table structuring.

Install dependencies:
```bash
pip install PyPDF2 pdfplumber python-docx pytesseract pandas sentence-transformers faiss-cpu langchain openai
```

**Code for Document Parsing**:
```python
import PyPDF2
import pdfplumber
from docx import Document
import pytesseract
from PIL import Image
import io
import pandas as pd
import os

def extract_text_from_pdf(file_path):
    """Extract text from a PDF (text-based or scanned)."""
    try:
        # First, try text-based PDF with pdfplumber
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            if text.strip():  # If text is extracted, return it
                return text

        # If no text (likely scanned), use OCR
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # Convert page to image for OCR
                img = page.to_image()
                img_path = "temp_page.png"
                img.save(img_path)
                text += pytesseract.image_to_string(Image.open(img_path))
                os.remove(img_path)
        return text
    except Exception as e:
        print(f"Error processing PDF {file_path}: {e}")
        return ""

def extract_text_from_docx(file_path):
    """Extract text from a DOCX file."""
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception as e:
        print(f"Error processing DOCX {file_path}: {e}")
        return ""

def extract_tables_from_pdf(file_path):
    """Extract tables from a PDF using pdfplumber."""
    try:
        tables = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                for table in page_tables:
                    # Convert table to DataFrame for easier handling
                    df = pd.DataFrame(table[1:], columns=table[0] if table else None)
                    tables.append(df)
        return tables
    except Exception as e:
        print(f"Error extracting tables from PDF {file_path}: {e}")
        return []

def process_document(file_path):
    """Process a document based on its extension."""
    ext = os.path.splitext(file_path)[1].lower()
    text, tables = "", []
    
    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
        tables = extract_tables_from_pdf(file_path)
    elif ext == ".docx":
        text = extract_text_from_docx(file_path)
    else:
        print(f"Unsupported format: {ext}")
        return None, None
    
    return text, tables
```

**Explanation**:
- **PDF Text Extraction**: `pdfplumber` is used first for text-based PDFs. If no text is extracted (indicating a scanned PDF), `pytesseract` performs OCR on page images.
- **DOCX Extraction**: `python-docx` extracts paragraph text from DOCX files.
- **Table Extraction**: `pdfplumber` extracts tables and converts them to `pandas` DataFrames for structured handling.
- **Error Handling**: Exceptions are caught to prevent crashes, with errors logged for debugging.

#### 2. Text Processing and Embedding
After extracting text and tables, we clean the text, chunk it, and store embeddings in a vector database using `sentence-transformers` and `FAISS`.

**Code for Text Processing and Embedding**:
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

def clean_text(text):
    """Clean extracted text (remove extra spaces, newlines, etc.)."""
    return " ".join(text.split())

def process_tables(tables):
    """Convert tables to text for embedding."""
    table_text = ""
    for i, df in enumerate(tables):
        table_text += f"\nTable {i+1}:\n{df.to_string()}\n"
    return table_text

def chunk_text(text, chunk_size=500, chunk_overlap=50):
    """Split text into chunks for embedding."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    return text_splitter.split_text(text)

def create_embeddings(chunks, model_name="all-MiniLM-L6-v2"):
    """Create embeddings for text chunks."""
    model = SentenceTransformer(model_name)
    embeddings = model.encode(chunks, show_progress_bar=True)
    return embeddings

def store_in_vector_db(chunks, embeddings):
    """Store embeddings in FAISS vector database."""
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index, chunks

def process_and_store(file_path):
    """Process document and store in vector DB."""
    text, tables = process_document(file_path)
    if not text:
        return None, None
    
    # Clean text and append table text
    text = clean_text(text)
    table_text = process_tables(tables)
    full_text = text + "\n" + table_text
    
    # Chunk and embed
    chunks = chunk_text(full_text)
    embeddings = create_embeddings(chunks)
    
    # Store in FAISS
    index, stored_chunks = store_in_vector_db(chunks, embeddings)
    return index, stored_chunks
```

**Explanation**:
- **Text Cleaning**: Removes redundant spaces and newlines.
- **Table Processing**: Converts tables to a text representation for embedding.
- **Chunking**: Uses `langchain`’s `RecursiveCharacterTextSplitter` to split text into manageable chunks (500 characters, 50 overlap).
- **Embedding**: `sentence-transformers` generates embeddings with a lightweight model (`all-MiniLM-L6-v2`).
- **Vector Storage**: `FAISS` stores embeddings for efficient similarity search.

#### 3. Retrieval and Generation
For retrieval, we query the FAISS index to find relevant chunks. For generation, we use a language model (e.g., via OpenAI’s API or xAI’s Grok API if available).

**Code for Retrieval and Generation**:
```python
from openai import OpenAI

def retrieve_chunks(query, index, chunks, model_name="all-MiniLM-L6-v2", top_k=5):
    """Retrieve top-k relevant chunks from vector DB."""
    model = SentenceTransformer(model_name)
    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding, top_k)
    return [chunks[i] for i in indices[0]]

def generate_response(query, retrieved_chunks, api_key):
    """Generate response using a language model."""
    client = OpenAI(api_key=api_key)
    context = "\n".join(retrieved_chunks)
    prompt = f"Context:\n{context}\n\nQuery:\n{query}\n\nAnswer:"
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content

def rag_query(file_path, query, api_key):
    """Full RAG pipeline: process, retrieve, generate."""
    index, chunks = process_and_store(file_path)
    if index is None:
        return "Failed to process document."
    
    retrieved_chunks = retrieve_chunks(query, index, chunks)
    response = generate_response(query, retrieved_chunks, api_key)
    return response
```

**Explanation**:
- **Retrieval**: Encodes the query and searches the FAISS index for the top-5 relevant chunks.
- **Generation**: Combines retrieved chunks into a prompt and queries a language model (e.g., GPT-4 via OpenAI).
- **API Integration**: Uses OpenAI’s API for simplicity; replace with xAI’s Grok API if available (refer to https://x.ai/api for details).

#### 4. Maintaining 96%+ Success Rate with New Formats
To ensure robustness and adaptability:
- **Fallback Mechanisms**:
  - If `pdfplumber` fails, fall back to `PyPDF2` or OCR.
  - For unsupported formats, log the issue and attempt to treat as plain text if possible.
- **Format Detection**:
  - Use `mimetypes` or `python-magic` to detect file types dynamically.
- **Preprocessing Checks**:
  - Validate file integrity (e.g., check if PDF is corrupted using `PyPDF2`).
- **Logging and Monitoring**:
  - Log parsing errors with details (file type, size, error type) to identify patterns in failures.
- **Extensibility**:
  - Create a modular parser interface to add support for new formats (e.g., `.txt`, `.md`).
- **Testing**:
  - Test with diverse datasets (e.g., 100+ documents of mixed types) to measure success rate.
  - Use automated tests to simulate corrupted or malformed files.

**Code for Format Detection and Fallback**:
```python
import mimetypes
import magic

def detect_file_type(file_path):
    """Detect file type using python-magic."""
    try:
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        return file_type
    except Exception as e:
        print(f"Error detecting file type: {e}")
        return None

def process_with_fallback(file_path):
    """Process document with fallback for unsupported formats."""
    file_type = detect_file_type(file_path)
    text, tables = None, None
    
    if "pdf" in file_type:
        text, tables = process_document(file_path)
    elif "wordprocessingml" in file_type:
        text, tables = process_document(file_path)
    else:
        # Fallback: try reading as plain text
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except:
            print(f"Failed to process {file_path} as text.")
    
    if text or tables:
        print(f"Successfully processed {file_path}")
    else:
        print(f"Failed to process {file_path}")
    
    return text, tables
```

**Explanation**:
- **Dynamic Detection**: `python-magic` identifies file types beyond extensions.
- **Fallback**: Attempts to read unknown formats as plain text.
- **Logging**: Tracks successes and failures for continuous improvement.

### Additional Notes
- **OCR Optimization**: For scanned PDFs, preprocess images (e.g., increase contrast) to improve `pytesseract` accuracy.
- **Table Extraction**: If `pdfplumber` struggles with complex tables, consider `tabula-py` as an alternative.
- **Scalability**: For large document sets, use a distributed vector database like `Milvus` instead of `FAISS`.
- **API Costs**: If using OpenAI or xAI’s API, monitor token usage to manage costs.
- **Success Rate**: Regularly update the system with new parsers for emerging formats and retrain embeddings if domain-specific terms arise.

### Example Usage
```python
file_path = "sample.pdf"
query = "What is the main topic of the document?"
api_key = "your-openai-api-key"

response = rag_query(file_path, query, api_key)
print(response)
```

This system provides a robust, extensible RAG pipeline that handles PDFs (text and scanned), DOCX files, and tables while maintaining high reliability for new formats. Let me know if you need deeper details on any component or help with specific use cases!

EXCEL IMPLEMENTATION
To extend the RAG system to handle Excel files (`.xlsx`, `.xls`), we need to modify the document ingestion process to parse Excel content, extract text and tables, and integrate them into the existing pipeline. Below, I’ll update the relevant parts of the system to include Excel file processing, focusing on extracting text from cells, handling tables (spreadsheets), and ensuring compatibility with the existing RAG framework. I’ll use the `openpyxl` library for Excel parsing and maintain the 96%+ success rate for new formats.

### Modifications to the RAG System

#### 1. Install Additional Dependency
Add `openpyxl` to parse Excel files:
```bash
pip install openpyxl
```

#### 2. Update Document Ingestion
We’ll add a function to extract text and tables from Excel files and integrate it into the `process_document` function. Excel files are inherently tabular, so we’ll treat each sheet as a table and extract text from cells for embedding.

**Updated Code for Document Parsing**:
```python
import PyPDF2
import pdfplumber
from docx import Document
import pytesseract
from PIL import Image
import io
import pandas as pd
import os
import openpyxl

def extract_text_from_pdf(file_path):
    """Extract text from a PDF (text-based or scanned)."""
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            if text.strip():
                return text
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                img = page.to_image()
                img_path = "temp_page.png"
                img.save(img_path)
                text += pytesseract.image_to_string(Image.open(img_path))
                os.remove(img_path)
        return text
    except Exception as e:
        print(f"Error processing PDF {file_path}: {e}")
        return ""

def extract_text_from_docx(file_path):
    """Extract text from a DOCX file."""
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception as e:
        print(f"Error processing DOCX {file_path}: {e}")
        return ""

def extract_text_from_excel(file_path):
    """Extract text and tables from an Excel file."""
    try:
        workbook = openpyxl.load_workbook(file_path, read_only=True)
        text = ""
        tables = []
        
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            # Extract all cell values as text
            for row in sheet.iter_rows(values_only=True):
                row_text = " ".join(str(cell) for cell in row if cell is not None)
                if row_text.strip():
                    text += row_text + "\n"
            
            # Convert sheet to DataFrame for table representation
            data = [[cell for cell in row] for row in sheet.iter_rows(values_only=True)]
            if data:
                df = pd.DataFrame(data[1:], columns=data[0] if data[0] else None)
                tables.append(df)
        
        return text, tables
    except Exception as e:
        print(f"Error processing Excel {file_path}: {e}")
        return "", []

def extract_tables_from_pdf(file_path):
    """Extract tables from a PDF using pdfplumber."""
    try:
        tables = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                for table in page_tables:
                    df = pd.DataFrame(table[1:], columns=table[0] if table else None)
                    tables.append(df)
        return tables
    except Exception as e:
        print(f"Error extracting tables from PDF {file_path}: {e}")
        return []

def process_document(file_path):
    """Process a document based on its extension."""
    ext = os.path.splitext(file_path)[1].lower()
    text, tables = "", []
    
    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
        tables = extract_tables_from_pdf(file_path)
    elif ext == ".docx":
        text = extract_text_from_docx(file_path)
    elif ext in [".xlsx", ".xls"]:
        text, tables = extract_text_from_excel(file_path)
    else:
        print(f"Unsupported format: {ext}")
        return None, None
    
    return text, tables
```

**Explanation**:
- **Excel Parsing**: `openpyxl` reads Excel files. For each sheet, we:
  - Extract text by concatenating non-empty cell values into a single string (for embedding).
  - Convert the sheet to a `pandas` DataFrame to treat it as a table.
- **Table Handling**: Each sheet is considered a table, with the first row assumed as headers (if present).
- **Error Handling**: Catches exceptions (e.g., corrupted files) and returns empty results to prevent crashes.
- **Integration**: The `process_document` function now supports `.xlsx` and `.xls` extensions.

#### 3. Update Format Detection and Fallback
We’ll modify the `detect_file_type` and `process_with_fallback` functions to recognize Excel files using MIME types.

**Updated Code for Format Detection**:
```python
import mimetypes
import magic

def detect_file_type(file_path):
    """Detect file type using python-magic."""
    try:
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        return file_type
    except Exception as e:
        print(f"Error detecting file type: {e}")
        return None

def process_with_fallback(file_path):
    """Process document with fallback for unsupported formats."""
    file_type = detect_file_type(file_path)
    text, tables = None, None
    
    if "pdf" in file_type:
        text, tables = process_document(file_path)
    elif "wordprocessingml" in file_type:
        text, tables = process_document(file_path)
    elif "spreadsheetml" in file_type or "excel" in file_type:
        text, tables = process_document(file_path)
    else:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except:
            print(f"Failed to process {file_path} as text.")
    
    if text or tables:
        print(f"Successfully processed {file_path}")
    else:
        print(f"Failed to process {file_path}")
    
    return text, tables
```

**Explanation**:
- **MIME Types**: Excel files typically have MIME types like `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (`.xlsx`) or `application/vnd.ms-excel` (`.xls`).
- **Fallback**: If an unknown format is detected, the system attempts to read it as plain text, ensuring robustness.

#### 4. Text Processing and Embedding (Unchanged)
The existing `process_and_store` function already handles text and tables generically:
- **Text**: Excel cell content is concatenated into a single string, cleaned, and chunked.
- **Tables**: Each sheet’s DataFrame is converted to text via `df.to_string()` in `process_tables`.
- **Embeddings**: The `sentence-transformers` model processes the combined text (cells + tables) without modification.

#### 5. Maintaining 96%+ Success Rate
To ensure Excel files don’t degrade the system’s reliability:
- **Validation**: Check file integrity using `openpyxl`’s `load_workbook` (catches corrupted files).
- **Fallback for Large Files**: For very large Excel files, use `openpyxl`’s `read_only=True` mode to reduce memory usage.
- **Error Logging**: Log specific errors (e.g., missing sheets, invalid cell formats) to identify failure patterns.
- **Testing**: Include Excel files in test datasets, covering:
  - Multiple sheets with varied data (text, numbers, formulas).
  - Corrupted or password-protected files (to test error handling).
  - Large files (e.g., 10,000+ rows) to ensure performance.
- **Extensibility**: The modular `process_document` function allows easy addition of new parsers (e.g., for CSV files).

#### 6. Example Usage
```python
file_path = "sample.xlsx"
query = "What is the main topic of the spreadsheet?"
api_key = "your-openai-api-key"

response = rag_query(file_path, query, api_key)
print(response)
```

**Expected Behavior**:
- The system extracts text from all cells across sheets and treats each sheet as a table.
- The text and table content are chunked, embedded, and stored in the FAISS index.
- The query retrieves relevant chunks (e.g., sheet data related to the topic) and generates a response.

### Additional Notes
- **Complex Excel Files**: If sheets contain charts or images, `openpyxl` won’t extract them. Consider `pytesseract` for embedded images if needed (similar to scanned PDFs).
- **Formulas**: `openpyxl` extracts computed values, not formulas, which is typically desired for RAG.
- **Performance**: For very large Excel files, consider `pandas` with `read_excel` for faster parsing, but `openpyxl` is more reliable for varied formats.
- **Success Rate**: Test with diverse Excel files (e.g., single-sheet, multi-sheet, mixed data types) to ensure the 96%+ success rate holds.

The updated system now handles Excel files seamlessly alongside PDFs and DOCX, maintaining robustness and extensibility. Let me know if you need further tweaks or specific Excel-related features (e.g., handling specific sheet types or formula parsing)!

CSV IMPLEMENTATION
To extend the RAG system to handle CSV files (`.csv`), we need to update the document ingestion process to parse CSV content, extract text and tabular data, and integrate them into the existing pipeline that already supports PDFs, DOCX, and Excel files. Below, I’ll modify the relevant parts of the system to include CSV file processing using the `pandas` library, ensuring text extraction, table handling, and compatibility with the RAG framework while maintaining the 96%+ success rate for new formats.

### Modifications to the RAG System

#### 1. Install Dependencies
The existing dependencies already include `pandas`, which we’ll use for CSV parsing. No additional installations are needed:
```bash
# Already installed: pandas, PyPDF2, pdfplumber, python-docx, pytesseract, openpyxl, sentence-transformers, faiss-cpu, langchain, openai
```

#### 2. Update Document Ingestion
We’ll add a function to extract text and tables from CSV files and integrate it into the `process_document` function. CSV files are inherently tabular, so we’ll treat the entire file as a single table and extract text from all cells for embedding, similar to Excel handling.

**Updated Code for Document Parsing**:
```python
import PyPDF2
import pdfplumber
from docx import Document
import pytesseract
from PIL import Image
import io
import pandas as pd
import os
import openpyxl
import csv

def extract_text_from_pdf(file_path):
    """Extract text from a PDF (text-based or scanned)."""
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            if text.strip():
                return text
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                img = page.to_image()
                img_path = "temp_page.png"
                img.save(img_path)
                text += pytesseract.image_to_string(Image.open(img_path))
                os.remove(img_path)
        return text
    except Exception as e:
        print(f"Error processing PDF {file_path}: {e}")
        return ""

def extract_text_from_docx(file_path):
    """Extract text from a DOCX file."""
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception as e:
        print(f"Error processing DOCX {file_path}: {e}")
        return ""

def extract_text_from_excel(file_path):
    """Extract text and tables from an Excel file."""
    try:
        workbook = openpyxl.load_workbook(file_path, read_only=True)
        text = ""
        tables = []
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            for row in sheet.iter_rows(values_only=True):
                row_text = " ".join(str(cell) for cell in row if cell is not None)
                if row_text.strip():
                    text += row_text + "\n"
            data = [[cell for cell in row] for row in sheet.iter_rows(values_only=True)]
            if data:
                df = pd.DataFrame(data[1:], columns=data[0] if data[0] else None)
                tables.append(df)
        return text, tables
    except Exception as e:
        print(f"Error processing Excel {file_path}: {e}")
        return "", []

def extract_text_from_csv(file_path):
    """Extract text and tables from a CSV file."""
    try:
        # Read CSV into DataFrame
        df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip')
        
        # Extract text from all cells
        text = ""
        for row in df.values:
            row_text = " ".join(str(cell) for cell in row if pd.notna(cell))
            if row_text.strip():
                text += row_text + "\n"
        
        # Treat the entire CSV as a single table
        tables = [df]
        
        return text, tables
    except UnicodeDecodeError:
        # Fallback for non-UTF-8 encodings
        try:
            df = pd.read_csv(file_path, encoding='latin1', on_bad_lines='skip')
            text = ""
            for row in df.values:
                row_text = " ".join(str(cell) for cell in row if pd.notna(cell))
                if row_text.strip():
                    text += row_text + "\n"
            tables = [df]
            return text, tables
        except Exception as e:
            print(f"Error processing CSV {file_path}: {e}")
            return "", []
    except Exception as e:
        print(f"Error processing CSV {file_path}: {e}")
        return "", []

def extract_tables_from_pdf(file_path):
    """Extract tables from a PDF using pdfplumber."""
    try:
        tables = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                for table in page_tables:
                    df = pd.DataFrame(table[1:], columns=table[0] if table else None)
                    tables.append(df)
        return tables
    except Exception as e:
        print(f"Error extracting tables from PDF {file_path}: {e}")
        return []

def process_document(file_path):
    """Process a document based on its extension."""
    ext = os.path.splitext(file_path)[1].lower()
    text, tables = "", []
    
    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
        tables = extract_tables_from_pdf(file_path)
    elif ext == ".docx":
        text = extract_text_from_docx(file_path)
    elif ext in [".xlsx", ".xls"]:
        text, tables = extract_text_from_excel(file_path)
    elif ext == ".csv":
        text, tables = extract_text_from_csv(file_path)
    else:
        print(f"Unsupported format: {ext}")
        return None, None
    
    return text, tables
```

**Explanation**:
- **CSV Parsing**: `pandas.read_csv` reads the CSV file into a DataFrame. We use `encoding='utf-8'` by default and `on_bad_lines='skip'` to handle malformed rows gracefully.
- **Text Extraction**: Iterates through DataFrame rows, concatenating non-null cell values into a single string for embedding.
- **Table Handling**: The entire CSV is treated as a single table (DataFrame), consistent with Excel sheet handling.
- **Error Handling**:
  - Handles `UnicodeDecodeError` by falling back to `latin1` encoding, common for CSVs.
  - Catches other exceptions (e.g., malformed CSVs, empty files) and returns empty results.
- **Integration**: The `process_document` function now supports `.csv` extensions.

#### 3. Update Format Detection and Fallback
We’ll modify the `detect_file_type` and `process_with_fallback` functions to recognize CSV files using MIME types.

**Updated Code for Format Detection**:
```python
import mimetypes
import magic

def detect_file_type(file_path):
    """Detect file type using python-magic."""
    try:
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        return file_type
    except Exception as e:
        print(f"Error detecting file type: {e}")
        return None

def process_with_fallback(file_path):
    """Process document with fallback for unsupported formats."""
    file_type = detect_file_type(file_path)
    text, tables = None, None
    
    if "pdf" in file_type:
        text, tables = process_document(file_path)
    elif "wordprocessingml" in file_type:
        text, tables = process_document(file_path)
    elif "spreadsheetml" in file_type or "excel" in file_type:
        text, tables = process_document(file_path)
    elif "csv" in file_type or "text/csv" in file_type:
        text, tables = process_document(file_path)
    else:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except:
            print(f"Failed to process {file_path} as text.")
    
    if text or tables:
        print(f"Successfully processed {file_path}")
    else:
        print(f"Failed to process {file_path}")
    
    return text, tables
```

**Explanation**:
- **MIME Types**: CSV files typically have the MIME type `text/csv`.
- **Fallback**: If an unknown format is detected, the system attempts to read it as plain text, ensuring robustness.
- **CSV Detection**: Explicitly checks for `csv` or `text/csv` in the MIME type to handle CSVs correctly.

#### 4. Text Processing and Embedding (Unchanged)
The existing `process_and_store` function remains unchanged:
- **Text**: CSV cell content is concatenated into a single string, cleaned, and chunked.
- **Tables**: The CSV’s DataFrame is converted to text via `df.to_string()` in `process_tables`.
- **Embeddings**: The `sentence-transformers` model processes the combined text (cells + table) without modification.

#### 5. Maintaining 96%+ Success Rate
To ensure CSV files don’t degrade the system’s reliability:
- **Validation**: Check file integrity using `pandas.read_csv` with error handling for malformed files.
- **Encoding Fallback**: Support multiple encodings (e.g., `utf-8`, `latin1`) to handle diverse CSV sources.
- **Error Logging**: Log specific errors (e.g., encoding issues, missing delimiters) to identify failure patterns.
- **Testing**: Include CSV files in test datasets, covering:
  - Various delimiters (e.g., commas, tabs, semicolons) using `pandas`’s `sep` parameter if needed.
  - Large files (e.g., 100,000+ rows) to ensure performance.
  - Malformed CSVs (e.g., missing headers, inconsistent columns) to test error handling.
- **Extensibility**: The modular `process_document` function supports adding new parsers (e.g., for TSV files).

#### 6. Example Usage
```python
file_path = "sample.csv"
query = "What is the main topic of the CSV data?"
api_key = "your-openai-api-key"

response = rag_query(file_path, query, api_key)
print(response)
```

**Expected Behavior**:
- The system extracts text from all cells in the CSV and treats the file as a single table.
- The text and table content are chunked, embedded, and stored in the FAISS index.
- The query retrieves relevant chunks (e.g., CSV rows related to the topic) and generates a response.

### Additional Notes
- **Delimiter Variations**: If CSVs use non-standard delimiters (e.g., tabs, semicolons), extend `extract_text_from_csv` to detect delimiters using `csv.Sniffer`:
  ```python
  import csv
  with open(file_path, 'r') as f:
      dialect = csv.Sniffer().sniff(f.read(1024))
      f.seek(0)
      df = pd.read_csv(file_path, sep=dialect.delimiter)
  ```
- **Large CSVs**: For very large files, use `pandas`’s `chunksize` parameter to process in chunks, reducing memory usage.
- **Performance**: `pandas` is efficient for CSVs, but test with large datasets to ensure scalability.
- **Success Rate**: Test with diverse CSVs (e.g., different encodings, sizes, and structures) to maintain the 96%+ success rate.

The updated system now handles CSV files seamlessly alongside PDFs, DOCX, and Excel files, maintaining robustness and extensibility. Let me know if you need further refinements or specific CSV-related features (e.g., handling multi-line cells or custom delimiters)!