import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Futbol Maç Analiz Sistemi", page_icon="⚽", layout="centered"
)

st.title("⚽ Futbol Maç Analiz & İstatistik Otomasyonu")
st.write(
    "Maç oranlarını girerek benzer istatistikleri ve maç geçmişlerini anında"
    " inceleyin."
)

# Girdi Alanları (Web Arayüzü İçin)
st.sidebar.header("Maç Parametreleri")
t1 = st.sidebar.text_input("Ev Sahibi / 1. Takım", "Arsenal")
t2 = st.sidebar.text_input("Deplasman / 2. Takım", "Manchester City")
oran = st.sidebar.text_input("Maç Oranı / Eşik Değer", "1.72")

if st.sidebar.button("Analizi Başlat", type="primary"):
  if t1 and t2:
    # Pandas ile analiz verileri
    veriler = {
        "Lig": ["TR 2026/2027", "TR 2026/2027", "TR 2026/2027"],
        "Ev Sahibi": [t1, "Galatasaray", t2],
        "Deplasman": [t2, "Fenerbahçe", "Beşiktaş"],
        "Oran": [oran, "1.80", "1.65"],
        "KG": ["Var", "Yok", "Var"],
        "2.5 Üst": ["Evet", "Hayır", "Evet"],
    }
    df = pd.DataFrame(veriler)

    st.subheader(f"📊 {t1} vs {t2} Analiz Raporu")
    st.write(f"Kullanılan Oran / Eşik: **{oran}**")
    st.dataframe(df, use_container_width=True)
  else:
    st.warning("Lütfen takım isimlerini eksiksiz girin.")
else:
  st.info(
      "Sol taraftaki menüden takımları ve oranı girip 'Analizi Başlat' butonuna"
      " basın."
  )
