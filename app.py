import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io

st.set_page_config(page_title="Assinador do General", layout="centered")
st.title("🖋️ Assinador de PDF - Ultra Fast")

# Upload dos arquivos
uploaded_pdf = st.file_uploader("Puxe o PDF aqui", type="pdf")
uploaded_sign = st.file_uploader("Puxe sua assinatura (PNG)", type=["png", "jpg"])

if uploaded_pdf and uploaded_sign:
    # Coordenadas (Aqui você ajusta onde a assinatura vai cair)
    # x, y, largura, altura
    posicao = st.slider("Ajuste a posição vertical da assinatura", 0, 800, 700)

    if st.button("Gerar PDF Assinado"):
        # Ler o PDF
        doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
        img_data = uploaded_sign.read()
        
        # Aplicar em todas as páginas (ou só na última, se preferir)
        for page in doc:
            # Define o retângulo onde a imagem será inserida
            # rect = (x0, y0, x1, y1)
            rect = fitz.Rect(400, posicao, 550, posicao + 50)
            page.insert_image(rect, stream=img_data)
        
        # Salvar o resultado
        out = io.BytesIO()
        doc.save(out)
        
        st.success("Feito! Agora é só baixar.")
        st.download_button(
            label="📥 Baixar PDF Assinado",
            data=out.getvalue(),
            file_name="documento_assinado.pdf",
            mime="application/pdf"
        )
