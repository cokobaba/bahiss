import streamlit as st
import pandas as pd
import numpy as np
import time
import re
from playwright.sync_api import sync_playwright
import matplotlib.pyplot as plt

# Sayfa Yapılandırması (Geniş Ekran)
st.set_page_config(page_title="Kapsamlı Oran Analiz Merkezi", page_icon="⚽", layout="wide")

# ----------------- SABİTLER VE LİSTELER -----------------
LIG_URL_HARITASI = {
    "Süper Lig": "https://www.oddsportal.com/football/turkey/super-lig/",
    "Premier Lig": "https://www.oddsportal.com/football/england/premier-league/",
    "La Liga": "https://www.oddsportal.com/football/spain/laliga/",
    "Serie A": "https://www.oddsportal.com/football/italy/serie-a/",
    "MLS": "https://www.oddsportal.com/football/usa/mls/",
    "Eredivisie": "https://www.oddsportal.com/football/netherlands/eredivisie/",
    "Bundesliga": "https://www.oddsportal.com/football/germany/bundesliga/"
}

DOSYA_HARITASI = {
    "Süper Lig": "super_lig_tum_sezonlar.xlsx",
    "Premier Lig": "premier_lig_tum_sezonlar.xlsx",
    "La Liga": "laliga_tum_sezonlar.xlsx",
    "Serie A": "serie_a_tum_sezonlar.xlsx",
    "MLS": "mls_tum_sezonlar.xlsx",
    "Eredivisie": "eredivisie_tum_sezonlar.xlsx",
    "Bundesliga": "bundesliga_tum_sezonlar.xlsx"
}

SUREL_LIG_TAKIMLARI = [
    "", "Alanyaspor", "Amedspor", "Basaksehir", "Besiktas", "Corum", 
    "Erzurumspor", "Eyupspor", "Fenerbahce", "Galatasaray", "Gaziantep", 
    "Genclerbirligi", "Goztepe", "Kasimpasa", "Kocaelispor", "Konyaspor", 
    "Rizespor", "Samsunspor", "Trabzonspor"
]

PREMIER_LIG_TAKIMLARI = [
    "", "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton", 
    "Chelsea", "Coventry", "Crystal Palace", "Everton", "Fulham", "Hull", 
    "Ipswich", "Leeds", "Liverpool", "Manchester City", "Manchester Utd", 
    "Newcastle", "Nottingham", "Sunderland", "Tottenham"
]

LA_LIGA_TAKIMLARI = [
    "", "Alaves", "Almeria", "Ath Bilbao", "Atl. Madrid", "Barcelona", 
    "Betis", "Celta Vigo", "Elche", "Espanyol", "Getafe", "Girona", 
    "Granada", "Las Palmas", "Mallorca", "Osasuna", "Rayo Vallecano", 
    "Real Madrid", "Real Sociedad", "Sevilla", "Valencia", "Villarreal"
]

SERIE_A_TAKIMLARI = [
    "", "AC Milan", "AS Roma", "Atalanta", "Bologna", "Cagliari", 
    "Como", "Fiorentina", "Frosinone", "Genoa", "Inter", "Juventus", 
    "Lazio", "Lecce", "Monza", "Napoli", "Parma", "Sassuolo", 
    "Torino", "Udinese", "Venezia"
]

EREDIVISIE_TAKIMLARI = [
    "", "Ajax", "AZ Alkmaar", "Cambuur", "Den Haag", "Excelsior", 
    "Feyenoord", "G.A. Eagles", "Groningen", "Heerenveen", "Nijmegen", 
    "PSV", "Sittard", "Sparta Rotterdam", "Telstar", "Twente", 
    "Utrecht", "Willem II", "Zwolle"
]

BUNDESLIGA_TAKIMLARI = [
    "", "Augsburg", "B. Monchengladbach", "Bayer Leverkusen", "Bayern Munich", 
    "Dortmund", "Eintracht Frankfurt", "Elversberg", "FC Koln", "Freiburg", 
    "Hamburger SV", "Hoffenheim", "Mainz", "Paderborn", "RB Leipzig", 
    "Schalke", "Stuttgart", "Union Berlin", "Werder Bremen"
]

def takim_listesi_getir(lig):
    if lig == "Süper Lig": return SUREL_LIG_TAKIMLARI
    elif lig == "Premier Lig": return PREMIER_LIG_TAKIMLARI
    elif lig == "La Liga": return LA_LIGA_TAKIMLARI
    elif lig == "Serie A": return SERIE_A_TAKIMLARI
    elif lig == "Eredivisie": return EREDIVISIE_TAKIMLARI
    elif lig == "Bundesliga": return BUNDESLIGA_TAKIMLARI
    return [""]

# Session State başlatma (Canlı maçtan gelen oranları tutmak için)
if 'm1_val' not in st.session_state: st.session_state['m1_val'] = ""
if 'm0_val' not in st.session_state: st.session_state['m0_val'] = ""
if 'm2_val' not in st.session_state: st.session_state['m2_val'] = ""

# ----------------- ANA BAŞLIK -----------------
st.title("⚽ Kapsamlı Oran Analiz Merkezi")
st.markdown("---")

# ----------------- YAN PANEL (KONTROL PANELİ) -----------------
st.sidebar.header("⚙️ Analiz Kontrol Paneli")

secilen_lig = st.sidebar.selectbox("Lig Seçimi", list(DOSYA_HARITASI.keys()))

mevcut_takimlar = takim_listesi_getir(secilen_lig)
takim1 = st.sidebar.selectbox("1. Takım (Opsiyonel)", mevcut_takimlar)
takim2 = st.sidebar.selectbox("2. Takım (Opsiyonel)", mevcut_takimlar)

st.sidebar.markdown("### 📊 Oran Girişleri")
m1_input = st.sidebar.text_input("MS1 Oran", value=st.session_state['m1_val'])
m0_input = st.sidebar.text_input("MS0 Oran", value=st.session_state['m0_val'])
m2_input = st.sidebar.text_input("MS2 Oran", value=st.session_state['m2_val'])

analiz_tetiklendi = st.sidebar.button("🚀 Analizi Başlat", type="primary")

# ----------------- GÜNÜN MAÇLARI SCRAPER MODÜLÜ -----------------
st.sidebar.markdown("---")
st.sidebar.subheader("🌐 Canlı Maç Çekme")

if st.sidebar.button("Oddsportal Maçlarını Çek"):
    url = LIG_URL_HARITASI.get(secilen_lig)
    with st.spinner(f"{secilen_lig} maçları taranıyor, lütfen bekleyin..."):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
                page = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36").new_page()
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
                time.sleep(5)
                
                try:
                    page.click("#onetrust-accept-btn-handler", timeout=2000)
                except:
                    pass

                for _ in range(5):
                    page.mouse.wheel(0, 1000)
                    time.sleep(0.5)

                match_data = page.evaluate("""
                    () => {
                        const rows = [];
                        const links = document.querySelectorAll('a[href*="/football/"]');
                        links.forEach(link => {
                            const href = link.getAttribute('href') || '';
                            const text = link.innerText ? link.innerText.trim() : '';
                            const lowerText = text.toLowerCase();
                            
                            if (lowerText.includes('outrights') || lowerText.includes('polski') || (text.includes('/') && !text.includes('-'))) {
                                return;
                            }
                            
                            if (href.includes('-vs-') || (href.split('/').length >= 6 && !href.includes('/results/') && !href.includes('/standings/'))) {
                                if (!text.includes('Finished') && !text.includes('FT')) {
                                    const lines = text.split('\\n').map(s => s.trim()).filter(Boolean);
                                    let parent = link.closest('div.flex') || link.parentElement;
                                    while (parent && parent.innerText && parent.innerText.split('\\n').length < 10) {
                                        parent = parent.parentElement;
                                    }
                                    const fullText = parent ? parent.innerText : text;
                                    if (fullText.length > 10 && !rows.some(r => r.fullText === fullText)) {
                                        rows.push({ fullText: fullText });
                                    }
                                }
                            }
                        });
                        return rows;
                    }
                """)
                browser.close()
            
            if match_data:
                st.sidebar.success(f"{len(match_data)} aktif maç bulundu!")
                secilen_mac_metni = st.sidebar.selectbox("Maç Seçin", [m['fullText'][:80] for m in match_data])
                
                # Eşleşen tam metni bul ve oranları çek
                secilen_full = next(m['fullText'] for m in match_data if m['fullText'][:80] == secilen_mac_metni)
                odds = [float(o.replace(',', '.')) for o in re.findall(r"\b\d{1,3}[,\.]\d{1,2}\b", secilen_full)]
                
                if len(odds) >= 3:
                    st.session_state['m1_val'] = str(odds[0])
                    st.session_state['m0_val'] = str(odds[1])
                    st.session_state['m2_val'] = str(odds[2])
                    st.rerun()
            else:
                st.sidebar.warning("Bu ligde aktif maç bulunamadı.")
        except Exception as e:
            st.sidebar.error(f"Hata oluştu: {e}")

# ----------------- ANALİZ MOTORU VE GÖRSELLEŞTİRME -----------------
if analiz_tetiklendi:
    dosya = DOSYA_HARITASI.get(secilen_lig)
    
    try:
        m1_hedef = float(m1_input.strip())
        m0_hedef = float(m0_input.strip())
        m2_hedef = float(m2_input.strip())
    except ValueError:
        st.error("Lütfen geçerli sayısal oranlar girin (örn: 2.01).")
        st.stop()

    try:
        df = pd.read_excel(dosya)
    except FileNotFoundError:
        st.error(f"Hata: '{dosya}' dosyası sunucuda bulunamadı!")
        st.stop()

    df_filtered = df.copy()
    
    if takim1 and takim2:
        df_filtered = df_filtered[
            df_filtered['Ev_Sahibi'].astype(str).str.contains(takim1, case=False, na=False) | 
            df_filtered['Deplasman'].astype(str).str.contains(takim1, case=False, na=False) |
            df_filtered['Ev_Sahibi'].astype(str).str.contains(takim2, case=False, na=False) | 
            df_filtered['Deplasman'].astype(str).str.contains(takim2, case=False, na=False)
        ]
    elif takim1:
        df_filtered = df_filtered[
            df_filtered['Ev_Sahibi'].astype(str).str.contains(takim1, case=False, na=False) | 
            df_filtered['Deplasman'].astype(str).str.contains(takim1, case=False, na=False)
        ]
    elif takim2:
        df_filtered = df_filtered[
            df_filtered['Ev_Sahibi'].astype(str).str.contains(takim2, case=False, na=False) | 
            df_filtered['Deplasman'].astype(str).str.contains(takim2, case=False, na=False)
        ]

    df_clean = df_filtered.dropna(subset=['MS1', 'MS0', 'MS2']).drop_duplicates(
        subset=['Sezon', 'Ev_Sahibi', 'Deplasman', 'Skor', 'MS1', 'MS0', 'MS2']
    ).copy()
    
    if df_clean.empty:
        st.warning("Kriterlere uygun eşleşen veri bulunamadı.")
        st.stop()

    def calculate_universal_distance(row):
        m1, m0, m2 = row['MS1'], row['MS0'], row['MS2']
        w1 = 4.0 if m1_hedef < 1.30 else (1.5 if m1_hedef < 2.20 else 1.0)
        w0 = 1.5 if m0_hedef > 5.0 else 1.0
        w2 = 2.0 if m2_hedef > 5.0 else 1.0
        
        d1 = w1 * abs(m1 - m1_hedef) / max(m1_hedef, 1.0)
        d2 = w0 * abs(m0 - m0_hedef) / max(m0_hedef, 1.0)
        d3 = w2 * abs(m2 - m2_hedef) / max(m2_hedef, 1.0)
        return np.sqrt(d1**2 + d2**2 + d3**2)

    df_clean['sapma_skoru'] = df_clean.apply(calculate_universal_distance, axis=1)
    
    filtrelenmis = pd.DataFrame()
    tolerans_adim = 0.20
    max_tolerans_siniri = 1.00
    
    while filtrelenmis.empty and tolerans_adim <= max_tolerans_siniri:
        filtrelenmis = df_clean[df_clean['sapma_skoru'] <= tolerans_adim]
        if filtrelenmis.empty:
            tolerans_adim += 0.15

    sonuclar = filtrelenmis.sort_values('sapma_skoru').copy()
    
    if sonuclar.empty:
        st.warning("Bu oranlara yakın hiçbir maç bulunamadı.")
        st.stop()
        
    sonuclar['Sonuc'] = np.select(
        [sonuclar['Ev_Gol'] > sonuclar['Dep_Gol'], sonuclar['Ev_Gol'] == sonuclar['Dep_Gol']],
        ['MS1', 'MS0'],
        default='MS2'
    )
    
    toplam_mac = len(sonuclar)
    ms1_sayi = (sonuclar['Sonuc'] == 'MS1').sum()
    ms0_sayi = (sonuclar['Sonuc'] == 'MS0').sum()
    ms2_sayi = (sonuclar['Sonuc'] == 'MS2').sum()
    
    ms1_yuzde = (ms1_sayi / toplam_mac) * 100
    ms0_yuzde = (ms0_sayi / toplam_mac) * 100
    ms2_yuzde = (ms2_sayi / toplam_mac) * 100

    # Arayüz Yerleşimi (İki Kolon: Sol Rapor/Tablo, Sağ Grafik)
    col1, col2 = st.columns([1.3, 0.7])

    with col1:
        st.subheader("📋 Detaylı Sonuç Raporu")
        if takim1 and takim2:
            baslik = f"{takim1.upper()} veya {takim2.upper()} ({secilen_lig})"
        elif takim1:
            baslik = f"{takim1.upper()} ({secilen_lig})"
        elif takim2:
            baslik = f"{takim2.upper()} ({secilen_lig})"
        else:
            baslik = f"GENEL LİG ANALİZİ ({secilen_lig})"
            
        st.info(f"**{baslik}** | Toplam Eşleşen Maç: **{toplam_mac}** | Tolerans: **{tolerans_adim:.2f}**")
        
        # Metrik Kutuları
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("MS1 (Ev Sahibi)", f"%{ms1_yuzde:.1f}", f"{ms1_sayi} Adet")
        m_col2.metric("MS0 (Beraberlik)", f"%{ms0_yuzde:.1f}", f"{ms0_sayi} Adet")
        m_col3.metric("MS2 (Deplasman)", f"%{ms2_yuzde:.1f}", f"{ms2_sayi} Adet")

        st.markdown("#### En Sık Görülen Skorlar")
        skor_df = pd.DataFrame(sonuclar['Skor'].value_counts().head(3).reset_index())
        skor_df.columns = ['Skor', 'Adet']
        st.dataframe(skor_df, hide_index=True)

    with col2:
        st.subheader("📊 Olasılık Grafiği")
        fig, ax = plt.subplots(figsize=(4, 3.5))
        kategoriler = ['MS1', 'MS0', 'MS2']
        oranlar = [ms1_yuzde, ms0_yuzde, ms2_yuzde]
        renkler = ['#3b82f6', '#f59e0b', '#10b981']

        bars = ax.bar(kategoriler, oranlar, color=renkler, width=0.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_ylim(0, 100)
        ax.set_ylabel('Yüzde (%)')

        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'%{height:.1f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=9, weight='bold')

        st.pyplot(fig)

    st.markdown("---")
    st.subheader("🔍 Eşleşen Tüm Benzer Maçlar")
    st.dataframe(sonuclar[['Sezon', 'Ev_Sahibi', 'Deplasman', 'Skor', 'MS1', 'MS0', 'MS2', 'sapma_skoru']], use_container_width=True)
else:
    st.info("Sol panelden lig/oran seçip **'Analizi Başlat'** butonuna basarak sonuçları görüntüleyebilirsin.")
