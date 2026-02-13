import streamlit as st
import fitz  # PyMuPDF
import io
import os
from PIL import Image, ImageChops

st.set_page_config(page_title="Assinador do General", page_icon="✏️", layout="wide")

# --- FUNÇÃO PARA LIMPAR BORDAS ---
def trim_signature(img):
    # Converte para RGBA para garantir canal alpha
    img = img.convert("RGBA")
    bg = Image.new(img.mode, img.size, (255, 255, 255, 0))
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()
    return img.crop(bbox) if bbox else img

# --- LÓGICA DE ASSINATURA FIXA ---
# Nome do arquivo que deve estar na mesma pasta do código no GitHub
NOME_ARQUIVO_FIXO = "assinatura_fixa.png"

st.sidebar.header("🖋️ Gestão de Assinatura")

# Tenta carregar a assinatura fixa primeiro
img_raw = None
if os.path.exists(NOME_ARQUIVO_FIXO):
    try:
        img_raw = Image.open(NOME_ARQUIVO_FIXO)
        st.sidebar.success(f"✅ '{NOME_ARQUIVO_FIXO}' carregada!")
        if st.sidebar.button("Trocar/Remover Fixa"):
            # Apenas um aviso, para trocar tem que apagar o arquivo no GitHub
            st.sidebar.warning("Para trocar, apague o arquivo no GitHub ou suba um novo com o mesmo nome.")
    except Exception as e:
        st.sidebar.error(f"Erro ao ler arquivo fixo: {e}")

# Se não achou a fixa, pede o upload
if img_raw is None:
    uploaded_sign = st.sidebar.file_uploader("Suba sua assinatura (PNG transparente)", type=["png", "jpg"])
    if uploaded_sign:
        img_raw = Image.open(uploaded_sign)

uploaded_pdf = st.sidebar.file_uploader("📄 Puxe o PDF da Galvocat", type="pdf")

if uploaded_pdf and img_raw:
    # Processamento de imagem e PDF
    doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
    page = doc[0]
    pdf_w, pdf_h = page.rect.width, page.rect.height

    # Limpa a assinatura (Tira o excesso de branco/transparência)
    img_sign = trim_signature(img_raw)
    sign_w, sign_h = img_sign.size
    aspect_ratio = sign_h / sign_w

    # --- CONTROLES ---
    st.sidebar.subheader("📐 Ajuste de Precisão")
    pos_x = st.sidebar.slider("Horizontal (X)", 0.0, float(pdf_w), float(pdf_w * 0.5))
    # pos_y agora é exatamente onde a "base" da assinatura encosta
    pos_y = st.sidebar.slider("Vertical (Y) - Linha", 0.0, float(pdf_h), float(pdf_h * 0.8))
    largura = st.sidebar.slider("Tamanho (Largura)", 10.0, 600.0, 180.0)
    altura = largura * aspect_ratio

    # --- PREVIEW CALIBRADO ---
    zoom = 2 # Aumenta a qualidade do preview
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img_preview = Image.open(io.BytesIO(pix.tobytes())).convert("RGBA")
    
    # Overlay da assinatura no preview
    overlay = Image.new("RGBA", img_preview.size, (0, 0, 0, 0))
    p_x, p_y = int(pos_x * zoom), int((pos_y - altura) * zoom)
    p_w, p_h = int(largura * zoom), int(altura * zoom)
    
    sign_res = img_sign.resize((p_w, p_h), Image.Resampling.LANCZOS)
    overlay.paste(sign_res, (p_x, p_y), sign_res)
    
    st.image(Image.alpha_composite(img_preview, overlay), caption="Preview Real", use_container_width=True)

    # --- FINALIZAÇÃO ---
    if st.button("🚀 Gerar PDF Assinado"):
        img_byte_arr = io.BytesIO()
        img_sign.save(img_byte_arr, format='PNG')
        
        # Insere exatamente nas coordenadas do preview
        rect_final = fitz.Rect(pos_x, pos_y - altura, pos_x + largura, pos_y)
        
        # Coloca na última página do documento
        target_page = doc[-1]
        target_page.insert_image(rect_final, stream=img_byte_arr.getvalue())
        
        out = io.BytesIO()
        doc.save(out)
        st.success("PDF pronto!")
        st.download_button("📥 Baixar Agora", out.getvalue(), "documento_assinado.pdf")

else:
    if img_raw is None:
        st.warning("⚠️ O sistema não encontrou 'assinatura_fixa.png'. Verifique se o nome do arquivo no GitHub está exatamente assim (tudo minúsculo).")
    else:
        st.info("Assinatura carregada! Agora só falta puxar o PDF.")
