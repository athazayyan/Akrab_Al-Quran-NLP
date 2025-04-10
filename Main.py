import streamlit as st
import pandas as pd
import re
import time
from collections import defaultdict

# Atur konfigurasi halaman
st.set_page_config(page_title="Pencarian Ayat Al-Quran (Smart Search)", layout="wide", initial_sidebar_state="collapsed")

st.title("🔍 Pencarian Ayat Al-Quran (Smart Search)")
st.markdown("*Menemukan ayat yang sesuai dengan pertanyaan atau situasi Anda*")

# Load dataset CSV (cached agar cepat)
@st.cache_data
def load_data():
    df = pd.read_csv("alquran_dengan_tafsir.csv", dtype=str)
    df['combined_text'] = (df['terjemahan'].fillna('') + ' ' + df['tafsir_kemenag_short'].fillna('')).str.lower()
    df['ayat_id'] = df['surat'] + '-' + df['ayat_ke']
    return df

# Stopwords
@st.cache_data
def get_stopwords():
    return {
        'aku', 'saya', 'kamu', 'dia', 'kita', 'mereka', 'ini', 'itu', 'yang', 'apa',
        'sama', 'tapi', 'ga', 'gak', 'tidak', 'nya', 'ku', 'mu', 'cuman', 'jadi',
        'aja', 'doang', 'banget', 'deh', 'dong', 'lho', 'loh', 'sih', 'kayak', 'gitu',
        'gini', 'udah', 'ntar', 'nanti', 'malah', 'emang', 'padahal', 'biar', 'buat',
        'lagi', 'pas', 'emangnya', 'serius', 'nah', 'ya', 'yah', 'weleh', 'dan', 'di', 'ke',
        'anjay', 'anjir', 'wkwk', 'haha', 'hehe', 'hihi', 'cie', 'ciee', 'adalah', 'dalam',
        'akan', 'dari', 'dengan', 'untuk', 'pada', 'oleh', 'seperti', 'jika', 'maka', 'atau',
        'namun', 'tetapi', 'karena', 'sebab', 'juga', 'bahwa', 'ketika', 'saat', 'harus', 'bisa',
        'dapat', 'banyak', 'sedikit', 'hampir', 'sangat', 'terlalu', 'sekali', 'mungkin', 'pasti',
        'selalu', 'sering', 'jarang', 'kadang', 'kadang-kadang', 'bagaimana', 'mengapa', 'kenapa',
        'siapa', 'gimana', 'yg'
    }

# Tema-tema
@st.cache_data
def get_themes():
    themes = {
        # Tema yang sudah ada sebelumnya
        "kesedihan": ["sedih", "sabar", "tenang", "pertolongan", "harapan", "duka", "pilu", "susah", "menangis", "kehilangan", "tertekan", "depresi", "patah hati", "kesepian"],
        "usaha": ["tugas", "buat", "kerja", "usaha", "berusaha", "upaya", "rajin", "berjuang", "coba", "keras", "pantang menyerah", "gigih", "tekun", "sungguh-sungguh", "konsisten"],
        "hubungan_sosial": ["kawan", "sahabat", "orang", "teman", "rekan", "tetangga", "kelompok", "partner", "keluarga", "saudara", "orangtua", "kakak", "adik", "kenalan", "kolega"],
        "kekecewaan": ["kecewa", "dikhianati", "sendiri", "gak ada", "ditinggal", "terluka", "putus asa", "hampa", "sia-sia", "diabaikan", "dilukai", "disakiti", "patah", "gagal"],
        "kebahagiaan": ["syukur", "nikmat", "bahagia", "senang", "gembira", "sukacita", "lega", "puas", "beruntung", "bangga", "tersenyum", "ceria", "bahagia", "bersyukur"],
        "ketakutan": ["takut", "khawatir", "cemas", "gelisah", "was-was", "lindung", "aman", "perlindungan", "teror", "ngeri", "panik", "trauma", "fobia", "takuti", "waspada"],
        "waktu": ["waktu", "hari", "seharian", "malam", "pagi", "sia-sia", "habis", "lewat", "cepat", "lama", "besok", "kemarin", "sekarang", "masa", "durasi", "jam", "menit"],
        "kelalaian": ["lalai", "lupa", "main", "sia-sia", "lengah", "hiburan", "game", "kosong", "lalaikan", "terbuai", "abai", "abaikan", "melalaikan", "terlena", "teralihkan"],
        "cinta": ["cinta", "sayang", "kasih", "pacar", "mantan", "rindu", "kangen", "bucin", "jatuh cinta", "kasmaran", "asmara", "pasangan", "romansa", "memuja", "terpesona"],
        "kebingungan": ["galau", "bingung", "bimbang", "gak tau", "gak jelas", "gundah", "gak ngerti", "pusing", "dilematis", "rancu", "membingungkan", "tidak pasti", "ragu", "dilema"],
        "motivasi": ["semangat", "bangkit", "percaya", "harapan", "berani", "mimpi", "tujuan", "fokus", "pantang menyerah", "ambisi", "impian", "cita-cita", "ingin", "masa depan", "tekad"],
        "keimanan": ["iman", "islam", "muslim", "sholat", "doa", "dzikir", "surga", "neraka", "taat", "Allah", "Rasul", "Al-Quran", "wahyu", "ibadah", "masjid", "ramadhan", "puasa"],
        "overthinking": ["overthinking", "kepikiran", "mikir terus", "kepala penuh", "gak bisa tidur", "cemas", "overthink", "pikiran berlebih", "prasangka", "asumsi", "terlalu banyak pikir"],
        "self_love": ["self love", "sayangi diri", "cinta diri", "healing", "damai", "tenangin", "me time", "butuh waktu", "jaga diri", "menghargai diri", "istirahat", "rehat", "diri sendiri"],
        "kemalasan": ["mager", "males", "nggak mood", "tiduran", "tidur terus", "gak niat", "rebahan", "menunda", "prokrastinasi", "lamban", "santai", "ogah", "malas-malasan", "bermalas-malasan"],
        "kesyukuran": ["syukur", "terima kasih", "nikmat", "cukup", "bahagia", "alhamdulillah", "lega", "beruntung", "bersyukur", "rezeki", "karunia", "anugerah", "berkah", "pemberian"],
        "kesabaran": ["sabar", "menahan", "tenang", "tahan", "menunggu", "tabah", "bertahan", "kuat", "uji", "ujian", "cobaan", "tantangan", "kesulitan", "tahap", "proses"],
        "pemaafan": ["maaf", "memaafkan", "ampun", "ampunan", "dimaafkan", "mengampuni", "memaklumi", "toleransi", "mengerti", "pengertian", "memahami", "pengampunan", "pemberian maaf"],
        "keadilan": ["adil", "merata", "seimbang", "keseimbangan", "hak", "kewajiban", "kesetaraan", "sama rata", "porsi", "bagian", "hukum", "aturan", "kebenaran", "keadilan", "pengadilan"],
        "pendidikan": ["belajar", "sekolah", "kuliah", "pendidikan", "ilmu", "pengetahuan", "mengajar", "guru", "dosen", "murid", "mahasiswa", "siswa", "kelas", "ujian", "tes", "nilai"],
        "rezeki": ["rezeki", "harta", "uang", "kekayaan", "penghasilan", "gaji", "berkat", "pemberian", "keuangan", "ekonomi", "bisnis", "usaha", "modal", "investasi", "tabungan"],

        # 20 Tema Baru
        "kegagalan": ["gagal", "kalah", "jatuh", "tidak berhasil", "hancur", "runtuh", "keok", "terpuruk", "menyerah", "minder", "down", "tak mampu", "lelet", "stagnan", "macet"],
        "keberanian": ["berani", "keberanian", "nyali", "tabah", "teguh", "kuat", "lawan", "hadapi", "tak gentar", "tangguh", "pemberani", "gagah", "perkasa", "gentleman", "jantan"],
        "penyesalan": ["menyesal", "salah", "nyesel", "khilaf", "keliru", "gak sengaja", "penyesalan", "sesal", "rugi", "kecewa diri", "bodoh", "telat sadar", "goblok", "konyol", "spilled tea"],
        "kepercayaan_diri": ["percaya diri", "pd", "yakin", "mantap", "optimis", " pede", "self esteem", "bangga diri", "kuat mental", "gak takut", "siap", "berdiri tegak", "jati diri", "identitas"],
        "perjuangan": ["berjuang", "lawan", "perjuangan", "struggle", "fight", "tanding", "giat", "mati-matian", "all out", "keras kepala", "ngotot", "push", "dorong", "rebel", "resist"],
        "kesehatan": ["sehat", "sakit", "sembuh", "kesehatan", "penyakit", "obat", "istirahat", "capek", "lelah", "energi", "stamina", "fit", "bugar", "pulih", "vitalitas"],
        "konflik": ["konflik", "ribut", "berantem", "cekcok", "musuh", "lawan", "bentrok", "gaduh", "drama", "panas", "tegang", "rusuh", "kacau", "perang", "debat"],
        "kehilangan_orang": ["kehilangan", "meninggal", "pergi", "ditinggal mati", "wafat", "kematian", "duka cita", "hilang", "berpisah", "selamanya", "kenangan", "luka", "pilu hati", "sendu"],
        "keberkahan": ["berkah", "keberkahan", "rahmat", "karunia", "limpah", "anugerah", "rezeki melimpah", "kebaikan", "hidayah", "petunjuk", "cahaya", "damai hati", "keajaiban", "mukjizat"],
        "pengendalian_diri": ["kontrol diri", "tahan", "sabar", "mengendalikan", "emosi", "marah", "jaga hati", "tenang diri", "sabarin", "chill", "cool", "steady", "ngamuk", "brake"],
        "harapan_baru": ["harapan", "baru", "fresh start", "mulai lagi", "bangkit lagi", "cerah", "optimisme", "asa", "mimpi baru", "jalan baru", "restart", "reborn", "turn over", "new leaf"],
        "kebencian": ["benci", "dendam", "marah", "jengkel", "sebel", "muak", "jijik", "geram", "emosi", "panas hati", "hate", "grudge", "sakit hati", "ngeri", "antipati"],
        "kebersamaan": ["bersama", "kebersamaan", "solid", "kompak", "tim", "gotong royong", "satu hati", "united", "bareng", "rame", "harmoni", "saling bantu", "support", "back up"],
        "keputusan": ["putuskan", "keputusan", "pilih", "tentukan", "decide", "resolusi", "jalan", "langkah", "pilihan", "opsi", "fix", "deal", "commit", "pastikan", "tegas"],
        "kebingungan_pilihan": ["bimbang", "gak yakin", "dilema", "dua hati", "ragu-ragu", "gamang", "gak jelas", "stuck", "bingung pilih", "overthink pilihan", "kabur", "blur", "lost", "clueless"],
        "keikhlasan": ["ikhlas", "rela", "menerima", "pasrah", "tawakal", "ridha", "tulus", "hati bersih", "tanpa pamrih", "legowo", "accept", "surrender", "pure", "jernih hati"],
        "kebanggaan": ["bangga", "kebanggaan", "puas", "prestasi", "sukses", "menang", "hebat", "juara", "top", "keren", "pride", "glory", "achieve", "tercapai", "epic"],
        "ketenangan": ["tenang", "damai", "calm", "santai", "peace", "relaks", "adem", "nyaman", "stabil", "harmoni", "quiet", "chill out", "sejuk hati", "lunak"],
        "perubahan": ["ubah", "perubahan", "berubah", "transformasi", "shift", "ganti", "reformasi", "evolusi", "move on", "adaptasi", "tweak", "renew", "upgrade", "revamp"],
        "tanggung_jawab": ["tanggung jawab", "tugas", "kewajiban", "beban", "komitmen", "janji", "wajib", "duty", "load", "amanah", "pegang", "jaga", "handle", "responsibility"],
         "teknologi": ["teknologi", "digital", "internet", "komputer", "laptop", "hp", "gadget", "software", "aplikasi", "coding", "program", "sistem", "online", "virtual", "cyber"],
        
        "investasi_saham": ["saham", "trading", "invest", "bursa", "pasar modal", "profit", "rugi", "chart", "analisis", "portofolio", "dividend", "broker", "bull", "bear", "market"],
        
        "emas_logam_mulia": ["emas", "logam mulia", "perhiasan", "investasi emas", "kadar", "karat", "antam", "pegadaian", "simpan", "jual beli", "nilai", "harga", "asset", "safe haven"],
        
        "penipuan": ["tipu", "bohong", "scam", "menipu", "palsu", "fake", "hoax", "manipulasi", "curang", "dusta", "kebohongan", "pura-pura", "licik", "culas", "korupsi"],
        
        "cryptocurrency": ["crypto", "bitcoin", "ethereum", "blockchain", "wallet", "mining", "coin", "token", "defi", "nft", "exchange", "trade", "hodl", "altcoin", "doge"],
        
        "startup": ["startup", "bisnis", "venture", "founder", "ceo", "unicorn", "scaling", "pivot", "growth", "investor", "pitch", "valuation", "funding", "scale up", "exit"]

    }
    return themes

df = load_data()
stopwords = get_stopwords()
themes_dict = get_themes()

@st.cache_data
def build_inverted_index(df):
    inverted_index = defaultdict(list)
    for idx, row in df.iterrows():
        words = set(row['combined_text'].split())
        for word in words:
            if len(word) > 1:
                inverted_index[word].append(idx)
    return inverted_index

inverted_index = build_inverted_index(df)

# Context lookup
@st.cache_data
def build_context_lookup(df):
    context_lookup = {}
    for idx, row in df.iterrows():
        surat, ayat = row['surat'], int(row['ayat_ke'])
        context_lookup[f"{surat}-{ayat}"] = {
            'prev': df.index[(df['surat'] == surat) & (df['ayat_ke'] == str(ayat-1))].tolist(),
            'next': df.index[(df['surat'] == surat) & (df['ayat_ke'] == str(ayat+1))].tolist()
        }
    return context_lookup

context_lookup = build_context_lookup(df)

# UI komponen
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        konteks = st.text_area("Ceritakan situasi atau masukkan kata kunci:", height=100, 
                             placeholder="Contoh: Saya sedang merasa putus asa dalam usaha yang saya lakukan...")
    with col2:
        jumlah_ayat = st.slider("Jumlah ayat:", min_value=1, max_value=7, value=3)
        with st.expander("Pengaturan Lanjutan"):
            use_themes = st.checkbox("Gunakan pencarian berdasarkan tema", value=True)
            include_context = st.checkbox("Pertimbangkan konteks ayat", value=True)
            consider_stemming = st.checkbox("Pertimbangkan kata dasar", value=True)
            tema_dipilih = st.multiselect("Filter tema:", options=list(themes_dict.keys()), default=[])

# Simpan riwayat dan cache
if 'shown_ayats' not in st.session_state:
    st.session_state.shown_ayats = set()
if 'search_history' not in st.session_state:
    st.session_state.search_history = {}
if 'search_cache' not in st.session_state:
    st.session_state.search_cache = {}

# Reset riwayat
if st.sidebar.button("Reset Riwayat Pencarian"):
    st.session_state.shown_ayats = set()
    st.session_state.search_history = {}
    st.session_state.search_cache = {}
    st.sidebar.success("Riwayat pencarian telah direset!")

# Menampilkan riwayat pencarian
with st.sidebar:
    st.header("Riwayat Pencarian")
    for i, query in enumerate(st.session_state.search_history.keys()):
        st.write(f"{i+1}. {query}")

def extract_keywords(text):
    text = re.sub(r'[^\w\s]', ' ', text)
    words = text.lower().split()
    return [word for word in words if word not in stopwords and len(word) > 1]

def detect_themes(keywords):
    detected_themes = {}
    for theme, related_words in themes_dict.items():
        score = 0
        for word in keywords:
            if word in related_words:
                score += 1
            elif consider_stemming and len(word) > 3:
                for theme_word in related_words:
                    if word in theme_word or theme_word in word:
                        score += 0.5
                        break
        if score > 0:
            detected_themes[theme] = score
    return {k: v for k, v in sorted(detected_themes.items(), key=lambda item: item[1], reverse=True)}

def calculate_relevance_fast(df, indices, keywords, theme_words=None):
    scores = pd.Series(0, index=df.index)
    for idx in indices:
        text = df.at[idx, 'combined_text']
        keyword_score = sum(3 if word in text else 0 for word in keywords)
        partial_score = 0
        if consider_stemming:
            text_words = text.split()
            for word in keywords:
                if len(word) > 3:
                    for tw in text_words:
                        if word in tw or tw in word:
                            partial_score += 1
                            break
        theme_score = sum(2 if word in text else 0 for word in theme_words) if use_themes and theme_words else 0
        
        context_score = 0
        if include_context:
            ayat_id = df.at[idx, 'ayat_id']
            context = context_lookup.get(ayat_id, {})
            for prev_idx in context.get('prev', []):
                prev_text = df.at[prev_idx, 'combined_text']
                context_score += sum(0.5 for word in keywords if word in prev_text)
            for next_idx in context.get('next', []):
                next_text = df.at[next_idx, 'combined_text']
                context_score += sum(0.5 for word in keywords if word in next_text)
        
        scores[idx] = keyword_score + (partial_score * 0.7) + theme_score + context_score
    return scores

def search_relevant_verses(query, top_n=50):
    start_time = time.time()
    
    cache_key = f"{query}-{jumlah_ayat}-{use_themes}-{include_context}-{consider_stemming}-{','.join(tema_dipilih)}"
    if cache_key in st.session_state.search_cache:
        return st.session_state.search_cache[cache_key]
    
    keywords = extract_keywords(query)
    detected_themes = detect_themes(keywords)
    
    if tema_dipilih:
        detected_themes = {theme: score for theme, score in detected_themes.items() if theme in tema_dipilih}
    
    theme_words = [word for theme in detected_themes for word in themes_dict[theme]] if use_themes else []
    
    relevant_indices = set()
    for word in keywords + theme_words:
        relevant_indices.update(inverted_index.get(word, []))
    
    if relevant_indices:
        scores = calculate_relevance_fast(df, relevant_indices, keywords, theme_words)
        results = df.loc[scores > 0].copy()
        results['relevance'] = scores[scores > 0]
        results = results.sort_values('relevance', ascending=False).head(top_n)
    else:
        results = df.head(0)
    
    end_time = time.time()
    search_time = end_time - start_time
    
    cache_result = (results, detected_themes, search_time)
    st.session_state.search_cache[cache_key] = cache_result
    return cache_result

if st.button("Cari Ayat") and konteks:
    if konteks not in st.session_state.search_history:
        st.session_state.search_history[konteks] = time.time()
    
    with st.expander("Detail Pencarian", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            keywords = extract_keywords(konteks)
            st.write("Kata Kunci Terdeteksi:")
            st.write(", ".join(keywords))
    
    results, detected_themes, search_time = search_relevant_verses(konteks)
    
    with st.expander("Detail Pencarian", expanded=False):
        with col2:
            st.write("Tema Terdeteksi:")
            for theme, score in detected_themes.items():
                st.write(f"- {theme.replace('_', ' ').title()}: {score:.1f}")
        st.write(f"Waktu pencarian: {search_time:.3f} detik")
        st.write(f"Jumlah ayat yang ditemukan: {len(results)}")
    
    filtered_results = results[~results['ayat_id'].isin(st.session_state.shown_ayats)]
    
    if filtered_results.empty:
        st.warning("Tidak ditemukan ayat baru yang relevan. Coba gunakan kata kunci yang berbeda atau reset riwayat pencarian.")
        if results.empty:
            st.info("Saran: Coba jelaskan situasi Anda dengan lebih detail atau gunakan kata kunci yang berbeda.")
        else:
            st.info("Anda telah melihat semua ayat yang relevan. Gunakan tombol 'Reset Riwayat Pencarian' untuk memulai ulang.")
    else:
        selected_results = filtered_results.head(jumlah_ayat)
        
        for _, row in selected_results.iterrows():
            st.session_state.shown_ayats.add(row['ayat_id'])
        
        for i, row in enumerate(selected_results.itertuples()):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(f"### {row.surat} - Ayat {row.ayat_ke}")
                st.write(f"Relevansi: {row.relevance:.2f}")
            with col2:
                st.markdown(f"<div style='text-align:right; font-size:24px; direction:rtl;'>{row.arab}</div>", unsafe_allow_html=True)
            st.markdown("**Terjemahan:**")
            st.info(row.terjemahan or "-")
            tab1, tab2, tab3 = st.tabs(["Tafsir Kemenag", "Tafsir Quraish Shihab", "Tafsir Jalalayn"])
            with tab1:
                st.write(row.tafsir_kemenag_short or "-")
            with tab2:
                st.write(row.tafsir_quraish or "-")
            with tab3:
                st.write(row.tafsir_jalalayn or "-")
            st.markdown("---")
    
    if 'relevance' in df.columns:
        df.drop(columns=['relevance'], inplace=True)
