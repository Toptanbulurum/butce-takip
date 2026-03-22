import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from io import BytesIO

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Zeki Bütçe Asistanı", layout="wide", page_icon="💰")
st.title("📅 Aylık & Yıllık Bütçe Yönetimi")

DB_FILE = "butce_verisi.json"

# --- VERİ YÖNETİMİ FONKSİYONLARI ---
def verileri_yukle():
    cols = ["Tarih", "Tip", "Kategori", "Miktar", "Not"]
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not data:
                    return pd.DataFrame(columns=cols)
                
                df = pd.DataFrame(data)
                df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')
                df = df.dropna(subset=['Tarih'])
                return df
        except Exception:
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def verileri_kaydet(df):
    df_to_save = df.copy()
    if not df_to_save.empty:
        # Tarih formatını JSON için stringe çevir
        df_to_save['Tarih'] = df_to_save['Tarih'].dt.strftime('%Y-%m-%d')
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(df_to_save.to_dict('records'), f, ensure_ascii=False, indent=4)

# Başlangıçta session_state kontrolü
if 'df' not in st.session_state:
    st.session_state.df = verileri_yukle()

# --- YAN PANEL: VERİ GİRİŞİ ---
st.sidebar.header("📥 Yeni İşlem")
tarih_input = st.sidebar.date_input("İşlem Tarihi", datetime.now())
islem_tipi = st.sidebar.radio("İşlem Tipi", ["Gelir", "Gider"])

if islem_tipi == "Gelir":
    kategori = st.sidebar.selectbox("Gelir Kaynağı", ["Maaş", "Nakit Girişi", "Ek Gelir", "Diğer"])
else:
    kategori = st.sidebar.selectbox("Gider Kategorisi", ["Market", "Kredi Kartı", "Kredi", "Nakit Harcama", "Fatura", "Eğlence", "Diğer Giderler"])

miktar = st.sidebar.number_input("Miktar (TL)", min_value=0.0, step=10.0)
not_ekle = st.sidebar.text_input("Not")

if st.sidebar.button("Kaydet"):
    yeni_data = {
        "Tarih": pd.to_datetime(tarih_input), 
        "Tip": islem_tipi, 
        "Kategori": kategori, 
        "Miktar": float(miktar), 
        "Not": not_ekle
    }
    
    # FutureWarning almamak için liste üzerinden ekleme yapıyoruz
    current_data = st.session_state.df.to_dict('records')
    current_data.append(yeni_data)
    st.session_state.df = pd.DataFrame(current_data)
    
    verileri_kaydet(st.session_state.df)
    st.sidebar.success("İşlem başarıyla kaydedildi!")
    st.rerun()

# --- SIFIRLAMA ---
st.sidebar.divider()
st.sidebar.subheader("⚙️ Veri Yönetimi")
onay_kutusu = st.sidebar.checkbox("Verileri silmeyi onaylıyorum")
if st.sidebar.button("🗑️ TÜM VERİLERİ SİL", type="primary", disabled=not onay_kutusu):
    st.session_state.df = pd.DataFrame(columns=["Tarih", "Tip", "Kategori", "Miktar", "Not"])
    verileri_kaydet(st.session_state.df)
    st.sidebar.warning("Tüm veriler temizlendi!")
    st.rerun()

# --- ANA EKRAN ---
if not st.session_state.df.empty:
    st.write("### 🔍 Verileri Filtrele")
    col_f1, col_f2 = st.columns(2)

    # Yılları ve ayları güvenle çek
    yillar = sorted(st.session_state.df['Tarih'].dt.year.unique(), reverse=True)
    secili_yil = col_f1.selectbox("Yıl Seçin", yillar)

    aylar_liste = {1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran", 
                   7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"}
    
    su_an_ay = datetime.now().month
    secili_ay_ad = col_f2.selectbox("Ay Seçin", list(aylar_liste.values()), index=su_an_ay-1)
    secili_ay_no = [k for k, v in aylar_liste.items() if v == secili_ay_ad][0]

    # Filtreleme
    mask = (st.session_state.df['Tarih'].dt.year == secili_yil) & (st.session_state.df['Tarih'].dt.month == secili_ay_no)
    filtreli_df = st.session_state.df[mask].copy()

    st.divider()
    if not filtreli_df.empty:
        gelir = filtreli_df[filtreli_df['Tip'] == 'Gelir']['Miktar'].sum()
        gider = filtreli_df[filtreli_df['Tip'] == 'Gider']['Miktar'].sum()
        fark = gelir - gider
        
        c1, c2, c3 = st.columns(3)
        c1.metric(f"💰 {secili_ay_ad} Gelir", f"{gelir:,.2f} TL")
        c2.metric(f"💸 {secili_ay_ad} Gider", f"{gider:,.2f} TL")
        c3.metric("📈 Net Durum", f"{fark:,.2f} TL", delta=fark)

        if gelir > 0:
            oran = min(gider / gelir, 1.0)
            st.write(f"**Bütçe Kullanım Oranı: %{oran*100:.1f}**")
            st.progress(oran)

        st.divider()
        g1, g2 = st.columns(2)
        
        with g1:
            st.subheader("📊 Harcama Dağılımı")
            gider_df = filtreli_df[filtreli_df['Tip'] == 'Gider']
            if not gider_df.empty:
                gider_ozet = gider_df.groupby('Kategori')['Miktar'].sum()
                st.bar_chart(gider_ozet)
            else:
                st.info("Bu ay hiç gider kaydı yok.")
        
        with g2:
            st.subheader("📑 İşlem Listesi")
            temp_df = filtreli_df.copy()
            temp_df['Tarih'] = temp_df['Tarih'].dt.strftime('%d.%m.%Y')
            st.dataframe(temp_df.sort_values('Tarih', ascending=False), width='stretch')

        # Excel Aktarma
        output = BytesIO()
        try:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                filtreli_df.to_excel(writer, index=False, sheet_name='Butce')
            excel_data = output.getvalue()
            st.download_button("📥 Excel Raporunu İndir", excel_data, f"butce_{secili_ay_ad}_{secili_yil}.xlsx")
        except:
            st.error("Excel oluşturulurken bir hata oluştu. Lütfen 'xlsxwriter' kütüphanesinin yüklü olduğundan emin olun.")
    else:
        st.warning(f"⚠️ {secili_ay_ad} {secili_yil} dönemi için henüz kayıt bulunamadı.")
else:
    st.info("👋 Hoş geldiniz! Sol panelden ilk işleminizi ekleyerek bütçenizi yönetmeye başlayın.")
