import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image, ImageChops

st.set_page_config(page_title="Assinador Calibrado do General", layout="wide")
st.title("🖋️ Assinador com Calibragem de Precisão")

# Função para remover bordas vazias da assinatura
def trim_signature(img):
    bg = Image.new(img.mode, img.size, img.getpixel((0,0)))
    diff = ImageChops.difference(img, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return img.crop(bbox)
    return img

st.sidebar.header("🕹️ Painel de Controle")
uploaded_pdf = st.sidebar.file_uploader("1. Puxe o PDF", type="pdf")
uploaded_sign = st.sidebar.file_uploader("2. Puxe a Assinatura", type=["png", "jpg"])

if uploaded_pdf and uploaded_sign:
    uploaded_pdf.seek(0)
    uploaded_sign.seek(0)
    
    doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
    pagina = doc[0]
    largura_pag, altura_pag = pagina.rect.width, pagina.rect.height

    # --- PROCESSAMENTO COM CALIBRAGEM ---
    img_sign = Image.open(uploaded_sign).convert("RGBA")
    # Corta os espaços vazios para a assinatura ficar "justa" no clique
    img_sign = trim_signature(img_sign)
    
    st.sidebar.subheader("📐 Ajuste Fino na Linha")
    pos_x = st.sidebar.slider("Eixo X (Horizontal)", 0, int(largura_pag), int(largura_pag * 0.5))
    # Ajuste de sensibilidade no Y para cravar na linha
    pos_y = st.sidebar.slider("Eixo Y (Vertical)", 0, int(altura_pag), int(altura_pag * 0.8))
    escala = st.sidebar.slider("Tamanho da Assinatura", 10, 1000, 200)
    
    rotacao_z = st.sidebar.slider("Girar (Graus)", -180, 180, 0)

    # Aplicar transformações
    img_sign = img_sign.rotate(-rotacao_z, expand=True)
    width, height = img_sign.size
    proporcao = height / width

    # --- PREVIEW ---
    col1, col2 = st.columns([1, 1])
    with col1:
        pix = pagina.get_pixmap()
        img_background = Image.open(io.BytesIO(pix.tobytes())).convert("RGBA")
        
        # Overlay para visualização precisa
        sign_preview = img_sign.copy()
        sign_preview.thumbnail((escala, escala))
        
        overlay = Image.new("RGBA", img_background.size, (0, 0, 0, 0))
        # O ajuste pos_y - (escala * proporcao) ajuda a alinhar a base da imagem na linha
        overlay.paste(sign_preview, (pos_x, pos_y - int(escala * proporcao)), sign_preview)
        
        st.image(Image.alpha_composite(img_background, overlay), use_container_width=True)

    with col2:
        if st.button("🚀 Gerar PDF Assinado"):
            img_byte_arr = io.BytesIO()
            img_sign.save(img_byte_arr, format='PNG')
            
            # Define o retângulo usando a base (pos_y) como referência para a linha
            rect_final = fitz.Rect(pos_x, pos_y - (escala * proporcao), pos_x + escala, pos_y)
            
            target_page = doc[-1]
            target_page.insert_image(rect_final, stream=img_byte_arr.getvalue())
            
            out = io.BytesIO()
            doc.save(out)
            st.success("Calibrado com sucesso!")
            st.download_button("📥 Baixar PDF", out.getvalue(), "documento_calibrado.pdf")
