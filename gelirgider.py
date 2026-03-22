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
            return json.load(f)
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

# --- ANA EKRAN: ANALİZ VE TAHMİN ---
df = pd.DataFrame(st.session_state.veriler)

if not df.empty:
    toplam_gelir = df[df['Tip'] == 'Gelir']['Miktar'].sum()
    toplam_gider = df[df['Tip'] == 'Gider']['Miktar'].sum()
    net_kalan = toplam_gelir - toplam_gider

    # 1. Özet Kartları
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Gelir", f"{toplam_gelir:,.2f} TL")
    c2.metric("Toplam Gider", f"{toplam_gider:,.2f} TL", delta=f"-{toplam_gider}", delta_color="inverse")
    c3.metric("Mevcut Durum (Net)", f"{net_kalan:,.2f} TL")

    # 2. ZEKİ TAHMİN MOTORU
    st.divider()
    st.subheader("🔮 Ay Sonu Tahmini & Birikim Analizi")
    
    col_tahmin, col_tavsiye = st.columns(2)
    
    with col_tahmin:
        birikim_orani = (net_kalan / toplam_gelir * 100) if toplam_gelir > 0 else 0
        st.write(f"**Mevcut Birikim Oranın:** %{birikim_orani:.1f}")
        st.progress(min(max(birikim_orani / 100, 0.0), 1.0))
        
        if net_kalan > 0:
            st.success(f"Bu hızla gidersen ay sonunda **{net_kalan:,.2f} TL** tasarruf etmiş olacaksın.")
        else:
            st.error("Dikkat! Harcamaların gelirini aşmış durumda.")

    with col_tavsiye:
        st.write("**Asistan Notu:**")
        if birikim_orani < 20:
            st.warning("Birikim oranın %20'nin altında. Harcamalarını gözden geçirebilirsin.")
        else:
            st.info("Harika gidiyorsun! Finansal sağlığın yerinde.")

    # 3. GRAFİKLER VE LİSTE
    st.divider()
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("📊 Gider Dağılımı")
        gider_df = df[df['Tip'] == 'Gider'].groupby('Kategori')['Miktar'].sum()
        st.bar_chart(gider_df)
    with g2:
        st.subheader("📑 Son İşlemler")
        # Güncel Streamlit parametresi: width='stretch'
        st.dataframe(df.tail(10), width='stretch')

    # 4. EXCEL AKTARMA VE SIFIRLAMA
    st.divider()
    # Excel oluşturma işlemi
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Butce_Raporu')
    
    col_down1, col_down2 = st.columns(2)
    col_down1.download_button(
        label="📥 Verileri Excel Olarak İndir",
        data=output.getvalue(),
        file_name="butce_raporum.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    if col_down2.button("🗑️ Tüm Verileri Sıfırla"):
        if st.checkbox("Gerçekten silmek istiyor musun?"):
            st.session_state.veriler = []
            verileri_kaydet([])
            st.rerun()
else:
    st.info("Analiz yapabilmem için sol menüden veri girişi yapmalısın.")
