import streamlit as st
from janome.tokenizer import Tokenizer
import csv
import os
from striprtf.striprtf import rtf_to_text

# 自作辞書読み込み（平文一致用）
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

# 辞書読み込み
def load_dicts():
    with open("dictionaries/pn.csv.m3.120408.trim", encoding="utf-8") as f:
        textbox = [s.rstrip() for s in f if s.count("\t") >= 2]

    with open("dictionaries/wago.121808.txt", encoding="utf-8") as f:
        textbox2 = [s.rstrip() for s in f]

    with open("dictionaries/JIWC-A_2019.csv", encoding="utf-8") as f:
        reader = csv.reader(f)
        feeldic = [row for row in reader][1:]

    return textbox, textbox2, feeldic

# 否定表現判定
def check_negation(idx, token_list):
    negate = False
    if idx+1 < len(token_list):
        next_token = token_list[idx+1]
        if next_token.surface in ["ない", "ぬ"] or next_token.base_form in ["ない", "ぬ"]:
            negate = True
    if idx+2 < len(token_list):
        if (token_list[idx+1].surface == "く" and token_list[idx+2].surface in ["ない", "ぬ"]):
            negate = True
    if idx+3 < len(token_list):
        if (token_list[idx+1].surface == "く" and token_list[idx+2].surface == "は" and token_list[idx+3].surface in ["ない", "ぬ"]):
            negate = True
    if idx+2 < len(token_list):
        if (token_list[idx+1].surface in ["では", "じゃ", "だ", "で"] and token_list[idx+2].surface in ["ない", "ぬ"]):
            negate = True
    return negate

# 感情分析処理
def userfeeling(user, textbox, textbox2, feeldic, custom_dict):
    pleasure = 0.0
    feel = [0, 0, 0, 0, 0, 0, 0]
    wow = 1 + user.count("!") + user.count("！")

    # ✅ ✅ 自作辞書 (平文一致で判定)
    for i, emotion in enumerate(["悲しみ", "恐怖", "怒り", "嫌悪", "信頼", "驚き", "喜び"]):
        for keyword in custom_dict[emotion]:
            if keyword in user:
                feel[i] += 1 * wow

    # 以降は形態素解析＋否定反転
    t = Tokenizer()
    token_list = list(t.tokenize(user))
    npwordcount = 0
    feelwordcount = 0

    for idx, token in enumerate(token_list):
        surface = token.surface
        part = token.part_of_speech
        base = token.base_form

        if surface in ["いい", "し"]: continue
        if "助詞" in part or "助動詞" in part or "非自立" in part: continue

        # 極性辞書
        for line in textbox:
            word, negaposi, *_ = line.split("\t")
            if surface == word or base == word:
                npwordcount += 1
                score = 0
                if negaposi == "p":
                    score = 0.3 * wow
                elif negaposi == "n":
                    score = -0.3 * wow
                elif negaposi == "?p?n":
                    score = 0.1 * wow
                if check_negation(idx, token_list):
                    score *= -1
                pleasure += score
                break
        else:
            for line in textbox2:
                if f"\t{surface}" in line:
                    negaposi, word = line.split("\t")
                    npwordcount += 1
                    score = 0
                    if "ポジ" in negaposi:
                        score = 0.3 * wow
                    elif "ネガ" in negaposi:
                        score = -0.3 * wow
                    if check_negation(idx, token_list):
                        score *= -1
                    pleasure += score
                    break

        # 感情辞書
        for i, emotion_row in enumerate(feeldic):
            if surface in emotion_row:
                feelwordcount += 1
                for j in range(7):
                    score = float(emotion_row[j+1]) * wow
                    if check_negation(idx, token_list):
                        score *= -1
                    feel[j] += score

    if npwordcount:
        pleasure /= npwordcount
    if feelwordcount:
        feel = [f / feelwordcount for f in feel]

    return pleasure, feel

# === Streamlit UI ===
st.title("感情分析Webアプリ")
user_input = st.text_area("文章を入力してください")

if st.button("分析する"):
    textbox, textbox2, feeldic = load_dicts()
    custom_dict = load_custom_dicts()
    pleasure, feel = userfeeling(user_input, textbox, textbox2, feeldic, custom_dict)
    emotion_labels = ["悲しみ", "恐怖", "怒り", "嫌悪", "信頼", "驚き", "喜び"]

    st.text(f"送信: {user_input}")
    st.text(f"ネガポジ: {pleasure:.2f}")

    # 結果を高い順にソート＋色付け
    sorted_emotions = sorted(zip(emotion_labels, feel), key=lambda x: x[1], reverse=True)
    max_value = sorted_emotions[0][1]
    min_value = sorted_emotions[-1][1]

    for i, (label, score) in enumerate(sorted_emotions):
        color = "black"
        if score == max_value:
            color = "red"

        st.markdown(f"<span style='color:{color}; font-weight:bold'>{label}: {score:.3f}</span>", unsafe_allow_html=True)
