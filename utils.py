# utils.py
import streamlit as st
import json
import fitz  # PyMuPDF
import easyocr
import streamlit.components.v1 as components
import io
import numpy as np
from PIL import Image
import html
import textwrap
import uuid # For unique immersive IDs

# --- NEW: Initialize EasyOCR reader ---
# This will be slow the first time it runs as it downloads the model
@st.cache_resource
def get_ocr_reader():
    return easyocr.Reader(['en'])

def process_image_ocr(file_bytes):
    """Extracts text from image bytes using EasyOCR."""
    try:
        reader = get_ocr_reader()
        image = Image.open(io.BytesIO(file_bytes))
        # Convert image to numpy array
        image_np = np.array(image)
        
        # Read text
        result = reader.readtext(image_np, detail=0, paragraph=True)
        text = "\n".join(result)
        return text
    except Exception as e:
        print(f"Error during OCR: {e}")
        st.error(f"Error processing image: {e}")
        return None

def pdf_to_text(uploaded_file, perform_ocr=False):
    """Extracts text from an uploaded PDF file using PyMuPDF (fitz).
       If perform_ocr is True, it will OCR the PDF pages.
    """
    try:
        text = ""
        file_bytes = uploaded_file.getvalue()
        
        if not perform_ocr:
            # Standard text extraction
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text()
        
        # If standard extraction fails or if OCR is explicitly requested
        if perform_ocr or not text:
            if not text:
                st.warning("No text found in PDF. Attempting OCR on PDF pages...")
            else:
                st.info("Performing OCR on scanned PDF...")
                
            text = ""
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                reader = get_ocr_reader()
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(dpi=300) # Render page to image
                    img_bytes = pix.tobytes("png")
                    
                    # Read text from image bytes
                    image = Image.open(io.BytesIO(img_bytes))
                    image_np = np.array(image)
                    img_result = reader.readtext(image_np, detail=0, paragraph=True)
                    text += "\n".join(img_result) + "\n"

        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        st.error(f"Error reading PDF: {e}")
        return None

# --- NEW: Main File Processing Function ---
def process_uploaded_file(uploaded_file, source_type):
    """Determines file type and routes to the correct text extractor."""
    
    if source_type == "pdf":
        # This is a standard PDF, try text extraction first
        return pdf_to_text(uploaded_file, perform_ocr=False)
    elif source_type == "ocr":
        # This is a "Handwritten Notes (PDF)", force OCR
        return pdf_to_text(uploaded_file, perform_ocr=True)
    else:
        st.error(f"Unsupported file type: {uploaded_file.type}")
        return None


def render_markmap_html(markdown_content):
    """Create HTML with enhanced Markmap visualization and render it."""
    if not markdown_content:
        st.warning("No mindmap content to display.")
        return

    markdown_content = markdown_content.replace('`', '\\`').replace('${', '\\${')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            #mindmap {{
                width: 100%;
                height: 500px; /* Reduced height for tabs */
                margin: 0;
                padding: 0;
            }}
        </style>
        <script src="https://cdn.jsdelivr.net/npm/d3@6"></script>
        <script src="https://cdn.jsdelivr.net/npm/markmap-view"></script>
        <script src="https://cdn.jsdelivr.net/npm/markmap-lib@0.14.3/dist/browser/index.min.js"></script>
    </head>
    <body>
        <svg id="mindmap"></svg>
        <script>
            window.onload = async () => {{
                try {{
                    const markdown = `{markdown_content}`;
                    const transformer = new markmap.Transformer();
                    const {{root}} = transformer.transform(markdown);
                    const mm = new markmap.Markmap(document.querySelector('#mindmap'), {{
                        maxWidth: 300,
                        color: (node) => {{
                            const level = node.depth;
                            return ['#0d98ba', '#0a7a96', '#085c73', '#063e4d'][level % 4];
                        }},
                        paddingX: 16,
                        autoFit: true,
                        initialExpandLevel: 2,
                        duration: 500,
                    }});
                    mm.setData(root);
                    mm.fit();
                }} catch (error) {{
                    console.error('Error rendering mindmap:', error);
                }}
            }};
        </script>
    </body>
    </html>
    """
    components.html(html_content, height=520, scrolling=False)


import streamlit as st
import html
import textwrap

import streamlit as st
import html
import textwrap

def render_flashcards(flashcard_data):
    """
    Renders flashcards with a CSS flip-on-hover animation in Streamlit.
    Supports both:
      - {"front": "...", "back": "..."}
      - {"keyword": "...", "definition": "..."}
    """

    # --- Handle empty or invalid data ---
    if not flashcard_data or 'flashcards' not in flashcard_data or not flashcard_data['flashcards']:
        st.warning("No flashcards available to display.")
        return

    # --- CSS for Flashcards ---
    card_css = """
    <style>
    .flashcard-container {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        justify-content: center;
        padding: 20px;
    }

    .flashcard {
        background-color: transparent;
        width: 280px;
        height: 180px;
        perspective: 1000px;
        border-radius: 15px;
    }

    .flashcard-inner {
        position: relative;
        width: 100%;
        height: 100%;
        text-align: center;
        transition: transform 0.6s ease;
        transform-style: preserve-3d;
        box-shadow: 0 6px 15px rgba(0,0,0,0.2);
        border-radius: 15px;
        cursor: pointer;
    }

    /* Flip effect */
    .flashcard:hover .flashcard-inner {
        transform: rotateY(180deg);
    }

    .flashcard-front, .flashcard-back {
        position: absolute;
        width: 100%;
        height: 100%;
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
        border-radius: 15px;
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 15px;
        box-sizing: border-box;
        font-family: "Segoe UI", sans-serif;
    }

    .flashcard-front {
        background-color: #0099cc;
        color: white;
        font-size: 1.1rem;
        font-weight: 600;
        border: 2px solid #00bcd4;
    }

    .flashcard-back {
        background-color: #1e1e1e;
        color: #ffffff;
        transform: rotateY(180deg);
        font-size: 0.95rem;
        text-align: left;
        line-height: 1.4;
        border: 2px solid #00bcd4;
    }

    /* Responsive layout */
    @media (max-width: 768px) {
        .flashcard {
            width: 90%;
            height: 160px;
        }
    }
    </style>
    """
    st.markdown(card_css, unsafe_allow_html=True)

    # --- Generate HTML for Flashcards ---
    html_content = '<div class="flashcard-container">'

    for card in flashcard_data['flashcards']:
        # Handle both structures (front/back) or (keyword/definition)
        front_text = html.escape(
            card.get('front') or card.get('keyword') or 'No Front Text'
        ).replace('\n', '<br>')

        back_text = html.escape(
            card.get('back') or card.get('definition') or 'No Back Text'
        ).replace('\n', '<br>')

        html_content += textwrap.dedent(f"""
        <div class="flashcard">
            <div class="flashcard-inner">
                <div class="flashcard-front">
                    <p>{front_text}</p>
                </div>
                <div class="flashcard-back">
                    <p>{back_text}</p>
                </div>
            </div>
        </div>
        """)

    html_content += "</div>"

    # --- Render HTML ---
    st.markdown(html_content, unsafe_allow_html=True)
