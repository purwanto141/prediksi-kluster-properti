import streamlit as st
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt

# 1. PENGATURAN ANTARMUKA (UI)
st.set_page_config(
    page_title="Prediksi Kluster Properti", 
    page_icon="🏢",
    layout="centered"
)

# 2. LOAD MODEL & SCALER
@st.cache_resource
def load_models():
    # Menghindari error jika file belum ada saat pengembangan
    try:
        model = joblib.load('model_kmeans.pkl')
        scaler = joblib.load('scaler_robust.pkl')
        return model, scaler
    except:
        return None, None

kmeans, scaler = load_models()

# Mapping nama kluster
NAMA_CLUSTER = {
    0: "Kluster 0 (Skala Kecil-Menengah / Ekonomis)",
    1: "Kluster 1 (Skala Menengah-Besar / Premium)",
    2: "Kluster 2 (Skala Makro / Elite)"
}

# Header Utama
st.title("🏢 Aplikasi Prediksi & Segmentasi Properti")
st.markdown("Analisis kategori kluster properti Anda secara instan, baik satuan maupun massal.")
st.divider()

if kmeans is None or scaler is None:
    st.error("❌ Gagal memuat model. Pastikan file 'model_kmeans.pkl' dan 'scaler_robust.pkl' berada di folder yang sama.")
    st.stop()

# 3. MEMBUAT NAVIGASI TAB
tab1, tab2 = st.tabs(["📝 Input Satuan (Single)", "📁 Input Massal (Batch Upload)"])

# ==================== TAB 1: INPUT SATUAN ====================
with tab1:
    st.subheader("Input Spesifikasi Properti")
    col1, col2 = st.columns(2)
    
    with col1:
        luas_tanah = st.number_input("Luas Tanah (m²)", min_value=1.0, value=150.0, step=10.0, key="single_lt")
        jarak_kota = st.number_input("Jarak ke Pusat Kota (Km)", min_value=0.1, value=10.0, step=0.5, key="single_jk")
    
    with col2:
        harga_jual = st.number_input("Harga Jual Beli / Nilai Pasar (Rp)", min_value=1_000_000, value=850_000_000, step=5_000_000, key="single_hj")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🔮 Prediksi Kluster Satuan", type="primary", use_container_width=True):
        input_data = np.array([[luas_tanah, harga_jual, jarak_kota]])
        input_scaled = scaler.transform(input_data)
        cluster_prediksi = int(kmeans.predict(input_scaled)[0])
        
        with st.container(border=True):
            st.success("### 🎉 Hasil Analisis")
            st.markdown(f"Properti ini masuk ke dalam:  \n### **{NAMA_CLUSTER[cluster_prediksi]}**")
        
        # Visualisasi Pie Chart (Hanya untuk input satuan)
        st.divider()
        st.subheader("📊 Statistik Pembanding Pasar")
        labels = ['Kluster 0 (Ekonomis)', 'Kluster 1 (Premium)', 'Kluster 2 (Elite)']
        sizes = [76.86, 16.22, 6.93]
        colors = ['#34495e', '#3498db', '#e74c3c']
        
        explode = [0, 0, 0]
        explode[cluster_prediksi] = 0.15
        
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('none')
        ax.set_facecolor('none')
        
        wedges, texts, autotexts = ax.pie(
            sizes, explode=explode, labels=labels, autopct='%1.1f%%',
            startangle=140, colors=colors, wedgeprops={'edgecolor': 'white', 'linewidth': 1.5},
            textprops={'color': 'grey' if st.get_option("theme.base") == "light" else 'white'}
        )
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_weight('bold')
            
        ax.set_title("Posisi Properti Anda dalam Struktur Pasar (%)", color='grey' if st.get_option("theme.base") == "light" else 'white')
        st.pyplot(fig)

# ==================== TAB 2: INPUT MASSAL (BATCH) ====================
with tab2:
    st.subheader("Upload File Properti")
    st.markdown("""
    Unggah file excel `.xlsx` atau `.csv` Anda. Pastikan file memiliki **3 kolom wajib** dengan nama berikut:
    * `Luas_Tanah`
    * `Harga_Jual`
    * `Jarak_Kota`
    """)
    
    # Tombol download template untuk memudahkan user
    template_data = pd.DataFrame({
        'Luas_Tanah':,
        'Harga_Jual':,
        'Jarak_Kota': [5.5, 12.0, 2.1]
    })
    
    st.download_button(
        label="📥 Download Template Excel",
        data=template_data.to_csv(index=False).encode('utf-8'),
        file_name="template_prediksi_properti.csv",
        mime="text/csv"
    )
    
    st.divider()
    
    # Komponen upload file
    uploaded_file = st.file_uploader("Pilih file CSV atau Excel", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            # Membaca format file secara dinamis
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
                
            # Validasi kolom wajib
            kolom_wajib = ['Luas_Tanah', 'Harga_Jual', 'Jarak_Kota']
            if not all(col in df.columns for col in kolom_wajib):
                st.error(f"❌ Struktur file salah! Pastikan file memiliki kolom: {', '.join(kolom_wajib)}")
            else:
                st.success("✅ File berhasil dimuat! Menampilkan 5 data pertama:")
                st.dataframe(df.head())
                
                # Tombol eksekusi prediksi massal
                if st.button("🔮 Jalankan Prediksi Massal", type="primary", use_container_width=True):
                    # Ambil data sesuai urutan fitur model: ['Luas_Tanah', 'Harga_Jual', 'Jarak_Kota']
                    X_batch = df[kolom_wajib].values
                    
                    # Transformasi scaling
                    X_scaled = scaler.transform(X_batch)
                    
                    # Prediksi cluster
                    predictions = kmeans.predict(X_scaled)
                    
                    # Tambahkan kolom hasil prediksi ke dataframe asli
                    df['ID_Kluster'] = predictions
                    df['Nama_Kluster'] = df['ID_Kluster'].map(NAMA_CLUSTER)
                    
                    st.divider()
                    st.subheader("🎉 Hasil Prediksi Massal")
                    st.dataframe(df)
                    
                    # Sediakan tombol download untuk hasil yang sudah diprediksi
                    # Konversi hasil ke Excel (menggunakan excel agar user kantoran lebih familiar)
                    @st.cache_data
                    def convert_df_to_excel(df_result):
                        import io
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_result.to_excel(writer, index=False, sheet_name='Hasil Prediksi')
                        return output.getvalue()
                        
                    excel_data = convert_df_to_excel(df)
                    
                    st.download_button(
                        label="📥 Download Hasil Prediksi (.xlsx)",
                        data=excel_data,
                        file_name="hasil_prediksi_kluster.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses file: {e}")
