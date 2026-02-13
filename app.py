import streamlit as st
import fitz  # PyMuPDF
import io
import os
from PIL import Image, ImageChops

st.set_page_config(page_title="Assinador Precisão General", layout="wide")

# --- FUNÇÃO DE LIMPEZA ---
def trim_signature(img):
    bg = Image.new(img.mode, img.size, img.getpixel((0,0)))
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()
    return img.crop(bbox) if bbox else img

# --- CARREGAMENTO DA ASSINATURA (FIXA OU UPLOAD) ---
st.sidebar.header("🖋️ Assinatura")
if os.path.exists("assinatura_fixa.png"):
    img_raw = Image.open("assinatura_fixa.png").convert("RGBA")
    st.sidebar.success("✅ Assinatura fixa carregada!")
else:
    uploaded_sign = st.sidebar.file_uploader("Suba sua assinatura (ou salve como 'assinatura_fixa.png')", type=["png", "jpg"])
    img_raw = Image.open(uploaded_sign).convert("RGBA") if uploaded_sign else None

uploaded_pdf = st.sidebar.file_uploader("📄 Puxe o PDF", type="pdf")

if uploaded_pdf and img_raw:
    doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
    page = doc[0]
    # Tamanho real do PDF em pontos (ex: 595 x 842 para A4)
    pdf_w, pdf_h = page.rect.width, page.rect.height

    # Limpa a assinatura e pega proporção
    img_sign = trim_signature(img_raw)
    sign_w, sign_h = img_sign.size
    aspect_ratio = sign_h / sign_w

    # --- CONTROLES COM AJUSTE DE ESCALA ---
    st.sidebar.subheader("📐 Ajuste Fino")
    # Agora os sliders usam as unidades REAIS do PDF
    pos_x = st.sidebar.slider("Eixo X", 0.0, float(pdf_w), float(pdf_w * 0.5), step=1.0)
    pos_y = st.sidebar.slider("Eixo Y (Base da linha)", 0.0, float(pdf_h), float(pdf_h * 0.85), step=1.0)
    largura_desejada = st.sidebar.slider("Largura da Assinatura", 10.0, 500.0, 150.0)
    altura_desejada = largura_desejada * aspect_ratio

    # --- PREVIEW CALIBRADO ---
    # Geramos o preview com zoom 2x para ter precisão visual
    zoom = 2
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_preview = Image.open(io.BytesIO(pix.tobytes())).convert("RGBA")
    
    # Criamos um overlay do mesmo tamanho do preview
    overlay = Image.new("RGBA", img_preview.size, (0, 0, 0, 0))
    
    # Ajustamos a posição da assinatura para a escala do preview
    preview_x = int(pos_x * zoom)
    # Subtraímos a altura porque o PDF conta de cima para baixo, mas queremos a base na linha
    preview_y = int((pos_y - altura_desejada) * zoom)
    preview_w = int(largura_desejada * zoom)
    preview_h = int(altura_desejada * zoom)
    
    sign_res = img_sign.resize((preview_w, preview_h), Image.Resampling.LANCZOS)
    overlay.paste(sign_res, (preview_x, preview_y), sign_res)
    
    st.subheader("Visualização Real (O que você vê aqui é o que sairá no arquivo)")
    st.image(Image.alpha_composite(img_preview, overlay), use_container_width=True)

    # --- BOTÃO DE GERAR ---
    if st.button("🚀 Gerar e Baixar PDF Assinado"):
        img_byte_arr = io.BytesIO()
        img_sign.save(img_byte_arr, format='PNG')
        
        # O retângulo final usa EXATAMENTE as coordenadas do slider
        rect_final = fitz.Rect(pos_x, pos_y - altura_desejada, pos_x + largura_desejada, pos_y)
        
        # Insere na última página
        target_page = doc[-1]
        target_page.insert_image(rect_final, stream=img_byte_arr.getvalue())
        
        out = io.BytesIO()
        doc.save(out)
        st.download_button("📥 Clique aqui para baixar", out.getvalue(), "final_calibrado.pdf", "application/pdf")
else:
    st.info("Aguardando PDF e Assinatura...")
