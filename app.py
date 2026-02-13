import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image

st.set_page_config(page_title="Assinador do General", layout="wide")
st.title("🖋️ Assinador com Preview em Tempo Real")

# --- BARRA LATERAL (CONFIGURAÇÕES) ---
st.sidebar.header("Configurações")
uploaded_pdf = st.sidebar.file_uploader("1. Puxe o PDF", type="pdf")
uploaded_sign = st.sidebar.file_uploader("2. Puxe a Assinatura (PNG)", type=["png", "jpg"])

if uploaded_pdf and uploaded_sign:
    # Abrir o PDF para leitura
    pdf_bytes = uploaded_pdf.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pagina = doc[0]  # Usamos a primeira página para o preview
    
    # Sliders para posicionamento
    st.sidebar.subheader("Ajuste de Posição")
    # Pegamos as dimensões da página para limitar os sliders
    largura_pag, altura_pag = pagina.rect.width, pagina.rect.height
    
    pos_x = st.sidebar.slider("Posição Horizontal (X)", 0, int(largura_pag), int(largura_pag * 0.7))
    pos_y = st.sidebar.slider("Posição Vertical (Y)", 0, int(altura_pag), int(altura_pag * 0.8))
    tamanho = st.sidebar.slider("Tamanho da Assinatura", 10, 300, 100)

    # --- ÁREA CENTRAL (PREVIEW) ---
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Visualização")
        # Criar preview da página como imagem
        pix = pagina.get_pixmap(matrix=fitz.Matrix(1, 1)) # Zoom de 1x
        img_preview = Image.open(io.BytesIO(pix.tobytes()))
        
        # Definir o retângulo da assinatura para o preview
        rect_assinatura = fitz.Rect(pos_x, pos_y, pos_x + tamanho, pos_y + (tamanho * 0.5))
        
        # Desenhar o retângulo no preview (opcional, mas ajuda)
        import PIL.ImageDraw as ImageDraw
        draw = ImageDraw.Draw(img_preview)
        draw.rectangle([pos_x, pos_y, pos_x + tamanho, pos_y + (tamanho * 0.5)], outline="red", width=5)
        
        st.image(img_preview, caption="Onde o retângulo vermelho está, sua assinatura ficaria.", use_container_width=True)

    with col2:
        st.subheader("Ações")
        if st.button("🚀 Gerar PDF Assinado"):
            # Aplicar a assinatura de verdade no documento
            sign_bytes = uploaded_sign.read()
            
            # Assinar apenas a última página (comum em contratos) ou todas?
            # Vamos colocar na ÚLTIMA página por padrão aqui:
            target_page = doc[-1] 
            target_page.insert_image(rect_assinatura, stream=sign_bytes)
            
            # Salvar em memória
            pdf_output = io.BytesIO()
            doc.save(pdf_output)
            doc.close()

            st.success("PDF processado com sucesso!")
            st.download_button(
                label="📥 Baixar Documento Assinado",
                data=pdf_output.getvalue(),
                file_name="assinado_pelo_general.pdf",
                mime="application/pdf"
            )
else:
    st.info("Aguardando o PDF e a imagem da assinatura na barra lateral... 👈")
