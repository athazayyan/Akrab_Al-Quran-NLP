import streamlit as st
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Set page title
st.title('Pencarian Ayat Al-Quran')

# Load model SBERT
@st.cache_resource
def load_model():
    return SentenceTransformer('paraphrase-mpnet-base-v2')

model = load_model()

# Data ayat Al-Quran dalam format dictionary (Arab - Terjemahan)
ayat_quran = {
    "إِنَّ مَعَ ٱلْعُسْرِ يُسْرًۭا": "Sesungguhnya bersama kesulitan ada kemudahan. (QS. Al-Insyirah: 6)",
    "وَلَا تَهِنُوا۟ وَلَا تَحْزَنُوا۟ وَأَنتُمُ ٱلْأَعْلَوْنَ إِن كُنتُم مُّؤْمِنِينَ": "Janganlah kamu bersikap lemah, dan janganlah (pula) kamu bersedih hati, padahal kamulah orang-orang yang paling tinggi derajatnya, jika kamu orang-orang yang beriman. (QS. Ali 'Imran: 139)",
    "لَا يُكَلِّفُ ٱللَّهُ نَفْسًۭا إِلَّا وُسْعَهَا": "Allah tidak membebani seseorang melainkan sesuai dengan kesanggupannya. (QS. Al-Baqarah: 286)",
    "وَقَالَ رَبُّكُمُ ٱدْعُونِىٓ أَسْتَجِبْ لَكُمْ": "Dan Tuhanmu berfirman, 'Berdoalah kepada-Ku, niscaya akan Aku perkenankan bagimu.' (QS. Al-Mu'min: 60)",
    "وَٱسْتَعِينُوا۟ بِٱلصَّبْرِ وَٱلصَّلَوٰةِ": "Dan mohonlah pertolongan (kepada Allah) dengan sabar dan salat. (QS. Al-Baqarah: 45)",
    "وَمَن يَتَّقِ ٱللَّهَ يَجْعَل لَّهُۥ مَخْرَجًۭا": "Barangsiapa bertakwa kepada Allah niscaya Dia akan membukakan jalan keluar baginya. (QS. At-Talaq: 2)",
    "وَعَلَى ٱللَّهِ فَتَوَكَّلُوٓا۟ إِن كُنتُم مُّؤْمِنِينَ": "Dan hanya kepada Allah hendaknya kamu bertawakkal, jika kamu benar-benar orang yang beriman. (QS. Al-Maidah: 23)",
    "إِنَّ ٱلَّذِينَ ءَامَنُوا۟ وَعَمِلُوا۟ ٱلصَّٰلِحَٰتِ سَيَجْعَلُ لَهُمُ ٱلرَّحْمَٰنُ وُدًّۭا": "Sesungguhnya orang-orang yang beriman dan beramal saleh, Allah Yang Maha Pengasih akan menanamkan dalam hati mereka rasa kasih sayang. (QS. Maryam: 96)",
    "إِنَّ ٱلصَّلَوٰةَ تَنْهَىٰ عَنِ ٱلْفَحْشَآءِ وَٱلْمُنكَرِ": "Sesungguhnya salat itu mencegah dari perbuatan keji dan mungkar. (QS. Al-Ankabut: 45)",
    "إِنَّ ٱللَّهَ مَعَ ٱلصَّٰبِرِينَ": "Sesungguhnya Allah bersama orang-orang yang sabar. (QS. Al-Baqarah: 153)"
}

# Embedding ayat
@st.cache_resource
def create_index():
    embeddings = np.array([model.encode(ayat) for ayat in ayat_quran.values()])
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index

index = create_index()

# Input user
query = st.text_input('Masukkan kata kunci pencarian:', 
                     'Saya sedang merasa sedih dan butuh motivasi')

# Slider untuk jumlah hasil yang ditampilkan
num_results = st.slider('Jumlah ayat yang ingin ditampilkan:', 1, 5, 3)

if st.button('Cari Ayat'):
    # Pencarian ayat
    query_embedding = model.encode(query).reshape(1, -1)
    D, I = index.search(query_embedding, num_results)
    
    # Tampilkan hasil
    st.subheader('Ayat yang relevan:')
    ayat_list = list(ayat_quran.items())
    
    for idx, i in enumerate(I[0]):
        arabic, translation = ayat_list[i]
        st.write(f"{idx+1}. {arabic}")
        st.write(f"   ➝ {translation}")
        st.write(f"   🔍 Tingkat kemiripan: {1/(1+D[0][idx]):.2%}")
        st.write("---")
