import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image, ImageOps

st.set_page_config(page_title="Assinador Pro do General", layout="wide")
st.title("🖋️ Assinador 3D - Controle Total")

# --- BARRA LATERAL (CONFIGURAÇÕES) ---
st.sidebar.header("🕹️ Painel de Controle")
uploaded_pdf = st.sidebar.file_uploader("1. Puxe o PDF", type="pdf")
uploaded_sign = st.sidebar.file_uploader("2. Puxe a Assinatura (PNG)", type=["png", "jpg"])

if uploaded_pdf and uploaded_sign:
    # Resetar o ponteiro do arquivo para garantir leitura
    uploaded_pdf.seek(0)
    uploaded_sign.seek(0)
    
    # Abrir PDF
    pdf_bytes = uploaded_pdf.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pagina = doc[0]
    largura_pag, altura_pag = pagina.rect.width, pagina.rect.height

    # --- CONTROLES DE POSIÇÃO E TAMANHO ---
    st.sidebar.subheader("📐 Dimensões e Posição")
    pos_x = st.sidebar.slider("Eixo X (Horizontal)", 0, int(largura_pag), int(largura_pag * 0.5))
    pos_y = st.sidebar.slider("Eixo Y (Vertical)", 0, int(altura_pag), int(altura_pag * 0.5))
    escala = st.sidebar.slider("Tamanho (Escala)", 10, 1000, 250)

    # --- CONTROLES DE ROTAÇÃO ---
    st.sidebar.subheader("🔄 Rotação e Perspectiva")
    rotacao_z = st.sidebar.slider("Girar no Papel (Graus)", -180, 180, 0)
    inclina_x = st.sidebar.slider("Inclinar (Perspectiva X)", -50, 50, 0)
    inclina_y = st.sidebar.slider("Inclinar (Perspectiva Y)", -50, 50, 0)

    # --- PROCESSAMENTO DA IMAGEM DA ASSINATURA ---
    img_sign = Image.open(uploaded_sign).convert("RGBA")
    
    # Aplicar Transformação de Perspectiva (Simulando Eixos X e Y)
    # Criamos uma matriz de transformação
    width, height = img_sign.size
    m = (1, inclina_x/100, 0, inclina_y/100, 1, 0)
    img_sign = img_sign.transform((width, height), Image.AFFINE, m, resample=Image.BICUBIC)
    
    # Aplicar Rotação Z
    img_sign = img_sign.rotate(-rotacao_z, expand=True)

    # --- ÁREA CENTRAL (PREVIEW) ---
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("👁️ Preview do Documento")
        pix = pagina.get_pixmap(matrix=fitz.Matrix(1, 1))
        img_background = Image.open(io.BytesIO(pix.tobytes())).convert("RGBA")
        
        # Redimensionar assinatura para o preview
        sign_preview = img_sign.copy()
        sign_preview.thumbnail((escala, escala))
        
        # Criar uma camada transparente para o "overlay"
        overlay = Image.new("RGBA", img_background.size, (0, 0, 0, 0))
        overlay.paste(sign_preview, (pos_x, pos_y), sign_preview)
        
        # Combinar
        preview_final = Image.alpha_composite(img_background, overlay)
        st.image(preview_final, caption="Visualização de como ficará no PDF", use_container_width=True)

    with col2:
        st.subheader("💾 Finalizar")
        if st.button("🚀 Gerar PDF Assinado"):
            # Converter a imagem processada de volta para bytes para o PyMuPDF
            img_byte_arr = io.BytesIO()
            img_sign.save(img_byte_arr, format='PNG')
            img_final_bytes = img_byte_arr.getvalue()

            # Definir o retângulo final com base na escala
            rect_final = fitz.Rect(pos_x, pos_y, pos_x + escala, pos_y + (escala * (height/width)))
            
            # Aplicar em todas as páginas ou só na última? Vamos na última por padrão
            target_page = doc[-1]
            target_page.insert_image(rect_final, stream=img_final_bytes)
            
            pdf_output = io.BytesIO()
            doc.save(pdf_output)
            doc.close()

            st.success("Prontinho, General!")
            st.download_button(
                label="📥 Baixar PDF Assinado",
                data=pdf_output.getvalue(),
                file_name="documento_assinado_pro.pdf",
                mime="application/pdf"
            )
else:
    st.info("General, joga o PDF e a imagem da sua assinatura ali na esquerda pra gente começar.")
