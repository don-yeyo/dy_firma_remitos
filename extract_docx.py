import zipfile
import xml.etree.ElementTree as ET
import os

docx_path = r"docs\Modelos Visuales (VLMs) Locales para Procesamiento de Remitos.docx"
output_path = r"docs\Modelos_Visuales_Texto.txt"

try:
    with zipfile.ZipFile(docx_path) as docx:
        xml_content = docx.read('word/document.xml')
        root = ET.fromstring(xml_content)
        
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        paragraphs = []
        for paragraph in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            texts = []
            for text in paragraph.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                if text.text:
                    texts.append(text.text)
            paragraphs.append("".join(texts))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(paragraphs))
        print(f"Texto extraido con exito en: {output_path}")
except Exception as e:
    print(f"Error: {e}")
