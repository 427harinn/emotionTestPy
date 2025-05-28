import streamlit as st
from janome.tokenizer import Tokenizer
import csv
import os
from striprtf.striprtf import rtf_to_text

def load_custom_dicts():
    emotions = ["悲しみ", "恐怖", "怒り", "嫌悪", "信頼", "驚き", "喜び"]
    emotion_dict = {}
    for emotion in emotions:
        filename = f"custom_dictionaries/{emotion}.rtf"
        if os.path.exists(filename):
            with open(filename, encoding="utf-8") as f:
                rtf_content = f.read()
                plain_text = rtf_to_text(rtf_content)
                words = [line.strip() for line in plain_text.splitlines() if line.strip()]
                emotion_dict[emotion] = words
        else:
            emotion_dict[emotion] = []
    return emotion_dict

def load_dicts():
    with open("dictionaries/pn.csv.m3.120408.trim", encoding="utf-8") as f:
        textbox = [s.rstrip() for s in f if s.count("\t") >= 2]

    with open("dictionaries/wago.121808.txt", encoding="utf-8") as f:
        textbox2 = [s.rstrip() for s in f]

    with open("dictionaries/JIWC-A_2019.csv", encoding="utf-8") as f:
        reader = csv.reader(f)
        feeldic = [row for row in reader][1:]

    return textbox, textbox2, feeldic

def userfeeling(user, textbox, textbox2, feeldic):
    pleasure = 0.0
    feel = [0, 0, 0, 0, 0, 0, 0]  # sad, afraid, angry, hate, trust, surprise, happy
    wow = 1 + user.count("!") + user.count("！")

    # 自作辞書（文全体に完全一致）で感情スコアを加算
    for i, emotion in enumerate(["悲しみ", "恐怖", "怒り", "嫌悪", "信頼", "驚き", "喜び"]):
        check = sum(1 for keyword in custom_dict[emotion] if keyword in user)
        if check > 0:
            feel[i] += check * wow

    npwordcount = 0
    feelwordcount = 0
    t = Tokenizer()
    for token in t.tokenize(user):
        surface = token.surface
        part = token.part_of_speech
        if surface in ["いい", "し"]: continue
        if "助詞" in part or "助動詞" in part or "非自立" in part: continue

        for line in textbox:
            word, negaposi, *_ = line.split("\t")
            if surface == word:
                npwordcount += 1
                if negaposi == "p": pleasure += 0.3 * wow
                elif negaposi == "n": pleasure += -0.3 * wow
                elif negaposi == "?p?n": pleasure += 0.1 * wow
                break
        else:
            for line in textbox2:
                if f"\t{surface}" in line:
                    negaposi, word = line.split("\t")
                    npwordcount += 1
                    if "ポジ" in negaposi: pleasure += 0.3 * wow
                    elif "ネガ" in negaposi: pleasure += -0.3 * wow
                    break

        for row in feeldic:
            if surface in row:
                feelwordcount += 1
                for i in range(7):
                    feel[i] += float(row[i+1]) * wow

    if npwordcount: pleasure /= npwordcount
    if feelwordcount:
        feel = [f / feelwordcount for f in feel]

    return pleasure, feel

# === Streamlit UI ===
st.title("感情分析Webアプリ")
user_input = st.text_area("文章を入力してください")

if st.button("分析する"):
    textbox, textbox2, feeldic = load_dicts()
    custom_dict = load_custom_dicts()
    pleasure, feel = userfeeling(user_input, textbox, textbox2, feeldic)
    emotion_labels = ["悲しみ", "恐怖", "怒り", "嫌悪", "信頼", "興奮", "喜び"]

    # 表示部分をCLI風に変換
    st.text(f"送信: {user_input}")
    st.text(f"想定: {pleasure:.2f} {feel}")

    # 感情強度の評価語を決定
    max_value = max(feel)
    if max_value >= 1:
        howmatch = "とても"
    elif max_value >= 0.6:
        howmatch = "やや"
    elif max_value >= 0.3:
        howmatch = "ほんのり"
    else:
        howmatch = ""

    # ポジネガ判定
    if pleasure == 0:
        sent_type = "平常 且つ "
    elif pleasure > 0:
        sent_type = "ポジティブ 且つ "
    else:
        sent_type = "ネガティブ 且つ "

    main_emotion_index = feel.index(max(feel))
    main_emotion = emotion_labels[main_emotion_index]

    # 一番強い感情を0にして次に強いものを探す
    feel[main_emotion_index] = 0
    second_emotion_index = feel.index(max(feel))
    second_emotion = emotion_labels[second_emotion_index]

    # 表示
    if max_value != 0:
        st.text(f"{sent_type}{main_emotion}が{howmatch}強い文章です。次に{second_emotion}が強いです。")
    else:
        st.text(f"{sent_type}無感情です。")


