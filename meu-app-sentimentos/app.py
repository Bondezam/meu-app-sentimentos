import streamlit as st
import spacy
from spacytextblob import spacytextblob
import sqlite3
import pandas as pd
from deep_translator import GoogleTranslator

# ================= ===================================
# NÍVEL 1: CONFIGURAÇÃO DO SPACY E BANCO DE DADOS SQLITE
# =====================================================

# Carrega o modelo de linguagem do spaCy e adiciona a extensão de sentimento
nlp = spacy.load("en_core_web_sm")
nlp.add_pipe('spacytextblob')

# Conecta ao banco de dados SQLite local
conn = sqlite3.connect("sentimentos.db", check_same_thread=False)
cursor = conn.cursor()

# Recria a tabela caso a estrutura antiga sem 'comentario_pt' ainda exista
cursor.execute("""
    CREATE TABLE IF NOT EXISTS avaliacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        comentario_pt TEXT,
        comentario_en TEXT,
        sentimento TEXT,
        polaridade REAL
    )
""")
conn.commit()

# Configuração da página do Streamlit
st.set_page_config(page_title="E-Commerce Sentiment Analysis", page_icon="🛒", layout="wide")


# ================= ===================================
# NÍVEL 2: INTERFACE GRÁFICA, PROCESSAMENTO E CHARTS
# =====================================================

st.title("🛒 Dashboard de Avaliações - E-Commerce")
st.markdown("Analise o feedback dos seus clientes em tempo real com **spaCy** e tradução automática.")

st.divider()

# Formulário de entrada para o comentário em português
st.subheader("Inserir Nova Avaliação")
comentario_pt = st.text_area("Digite o comentário do cliente (em português):", placeholder="Ex: Produto excelente! Entrega rápida e ótima qualidade.")

if st.button("Analisar Sentimento", type="primary"):
    if comentario_pt.strip():
        # Traduz o texto em português para o inglês
        comentario_en = GoogleTranslator(source='pt', target='en').translate(comentario_pt)

        # Processa o texto traduzido com o spaCy
        doc = nlp(comentario_en)
        polaridade = doc._.blob.polarity  # Varia de -1.0 a 1.0

        # Classificação do sentimento com base na polaridade
        if polaridade > 0.1:
            sentimento = "Satisfeito 🟢"
        elif polaridade < -0.1:
            sentimento = "Não Satisfeito 🔴"
        else:
            sentimento = "Neutro ⚪"

        # Salva o resultado no banco de dados SQLite
        try:
            cursor.execute(
                "INSERT INTO avaliacoes (comentario_pt, comentario_en, sentimento, polaridade) VALUES (?, ?, ?, ?)",
                (comentario_pt, comentario_en, sentimento, polaridade)
            )
            conn.commit()
        except sqlite3.OperationalError:
            # Caso o banco estivesse com a tabela antiga, reseta e tenta inserir novamente
            cursor.execute("DROP TABLE IF EXISTS avaliacoes")
            cursor.execute("""
                CREATE TABLE avaliacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    comentario_pt TEXT,
                    comentario_en TEXT,
                    sentimento TEXT,
                    polaridade REAL
                )
            """)
            cursor.execute(
                "INSERT INTO avaliacoes (comentario_pt, comentario_en, sentimento, polaridade) VALUES (?, ?, ?, ?)",
                (comentario_pt, comentario_en, sentimento, polaridade)
            )
            conn.commit()

        # Exibição do resultado
        st.success(f"Avaliação registrada com sucesso! **Status:** {sentimento}")
        st.write(f"**Tradução para processamento:** *\"{comentario_en}\"*")
        st.metric("Score de Polaridade", f"{polaridade:.2f}")
    else:
        st.warning("Por favor, digite um comentário antes de analisar.")

st.divider()

# Recuperação dos dados do banco
try:
    df = pd.read_sql_query("SELECT * FROM avaliacoes", conn)
except Exception:
    df = pd.DataFrame()

st.subheader("📊 Métricas Gerais do E-Commerce")

if not df.empty:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Contagem por Categoria")
        contagem_sentimentos = df["sentimento"].value_counts()
        st.dataframe(contagem_sentimentos, use_container_width=True)

    with col2:
        st.markdown("### Distribuição do Nível de Satisfação")
        st.bar_chart(contagem_sentimentos, color="#1f77b4")

    st.subheader("📋 Últimas Avaliações Registradas")
    st.dataframe(df.sort_values(by="id", ascending=False), use_container_width=True)
else:
    st.info("Nenhuma avaliação cadastrada no banco de dados até o momento.")