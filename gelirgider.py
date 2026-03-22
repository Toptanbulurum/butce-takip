import streamlit as st
import pandas as pd
import json
import os
from io import BytesIO

# Sayfa Ayarları
st.set_page_config(page_title="Zeki Bütçe Asistanı", layout="wide")
st.title("🤖 Zeki Bütçe ve Birikim Asistanı")

DB_FILE = "butce_verisi.json"

def verileri_yukle():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def verileri_kaydet(kayitlar):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(kayitlar, f, ensure_ascii=False, indent=4)

if 'veriler' not in st.session_state:
    st.session_state.veriler = verileri_yukle()

# --- YAN PANEL: VERİ GİRİŞİ ---
st.sidebar.header("📥 İşlem Girişi")
islem_tipi = st.sidebar.radio("İşlem Tipi", ["Gelir", "Gider"])

if islem_tipi == "Gelir":
    kategori = st.sidebar.selectbox("Gelir Kaynağı", ["Maaş", "Nakit Girişi", "Ek Gelir", "Diğer"])
else:
    kategori = st.sidebar.selectbox("Gider Kategorisi", ["Market", "Kredi Kartı", "Kredi", "Nakit Harcama", "Diğer Giderler"])

miktar = st.sidebar.number_input("Miktar (TL)", min_value=0.0, step=100.0)
not_ekle = st.sidebar.text_input("Not (Opsiyonel)")

if st.sidebar.button("Kaydet"):
    st.session_state.veriler.append({"Tip": islem_tipi, "Kategori": kategori, "Miktar": miktar, "Not": not_ekle})
    verileri_kaydet(st.session_state.veriler)
    st.sidebar.success(f"{kategori} başarıyla eklendi!")
    st.rerun()

# --- ANA EKRAN: ANALİZ ---
df = pd.DataFrame(st.session_state.veriler)

if not df.empty:
    toplam_gelir = df[df['Tip'] == 'Gelir']['Miktar'].sum()
    toplam_gider = df[df['Tip'] == 'Gider']['Miktar'].sum()
    net_kalan = toplam_gelir - toplam_gider

    # 1. Özet Kartları
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Gelir", f"{toplam_gelir:,.2f} TL")
    c2.metric("Toplam Gider", f"{toplam_gider:,.2f} TL")
    c3.metric("Mevcut Durum (Net)", f"{net_kalan:,.2f} TL")

    # 2. Grafik ve Liste
    st.divider()
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("📊 Gider Dağılımı")
        gider_df = df[df['Tip'] == 'Gider'].groupby('Kategori')['Miktar'].sum()
        if not gider_df.empty:
            st.bar_chart(gider_df)
    with g2:
        st.subheader("📑 Son İşlemler")
        # HATALI KISIM BURADA DÜZELTİLDİ:
        st.dataframe(df.tail(10), width='stretch')

    # 3. Excel İndir ve Sıfırla
    st.divider()
    col_down1, col_down2 = st.columns(2)
    
    # Excel Hazırlama
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Rapor')
    
    col_down1.download_button(
        label="📥 Verileri Excel Olarak İndir",
        data=output.getvalue(),
        file_name="butce.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    if col_down2.button("🗑️ Tüm Verileri Sıfırla"):
        verileri_kaydet([]) 
        st.session_state.veriler = [] 
        st.rerun() 
else:
    st.info("Analiz yapabilmem için sol menüden veri girişi yapmalısın.")
