from janome.tokenizer import Tokenizer
import csv

def textcheck(user,boxname,check=0): #文中にリスト内の単語が含まれるか判定する関数
  for boxword in boxname:
    if user.find(boxword)!=-1:check=check+1
  return check

def userfeeling(user): #ユーザーの感情を読み取る関数(例:■ね→嫌悪,怒り)
  pleasure=0.0
  sad=afraid=angry=hate=trust=surprise=happy=0 #感情の定義
  feel=[sad,afraid,angry,hate,trust,surprise,happy]

  wow=1
  for s in user:
    if s=="!" or s=="！":wow+=1

  happybox=["かわい","好","良","喜","良","楽し","嬉","いい","素敵","おしゃれ"]#
  sadbox=["悲","かなし","死","失敗","泣","辛","つらい","不安","ごめん"]
  angrybox=["怒","嫌い","殺","苛","イライラ","最低","死ね","馬鹿","たたく","殴る"]
  hatebox=["不快","嫌悪","嫌","目障り","ゴミ","消えろ","死ね","殺","シャットダウン","拷問","たたく","殴る","犯す"]
  afraidbox=["怖","こわい","不安","助けて","ごめん"]
  surprisebox=["びっくり","すごい","驚","意外","えっ","わっ","！？"]
  trustbox=["信","好き","付き合","任せ"]

  for i,box in zip(range(len(feel)),[sadbox,afraidbox,angrybox,hatebox,trustbox,surprisebox,happybox]):
    check=textcheck(user,box,0)
    if check>0:feel[i]+=check*wow

  with open("dictionaries/pn.csv.m3.120408.trim", encoding="utf-8") as f: #極性辞書(名詞編)
    textbox=[s.rstrip() for s in f.readlines()]
  with open("dictionaries/wago.121808.txt", encoding="utf-8") as f: #極性辞書(用語編)
    textbox2=[s.rstrip() for s in f.readlines()]
  with open("dictionaries/JIWC-A_2019.csv", encoding="utf-8") as f: #感情辞書
    reader=csv.reader(f)
    feeldic=[row for row in reader]
  del feeldic[0]

  npwordcount=0
  feelwordcount=0
  t=Tokenizer()
  for token in t.tokenize(user):
    check=0
    if token.surface=="いい":continue #判定無視
    if token.surface=="し":continue
    if token.part_of_speech.find("助詞")!=-1 or token.part_of_speech.find("助動詞")!=-1 or token.part_of_speech.find("非自立")!=-1:continue
    for i in range(len(textbox)):  # 極性辞書(名詞編)の判定
        line = textbox[i].strip()
        if not line or line.count("\t") < 2:
            continue  # 項目数が足りない行をスキップ
        word, negaposi, _ = line.split("\t")
        if token.surface == word:
            npwordcount += 1
            check = 1
            if negaposi == "e": pleasure += 0 * wow
            elif negaposi == "p": pleasure += 0.3 * wow
            elif negaposi == "n": pleasure += -0.3 * wow
            elif negaposi == "?p?n": pleasure += 0.1 * wow
            break

    if check==0: #↑になかった場合のみ
      for i in range(len(textbox2)): #極性辞書(用語編)の判定
        if "\t"+token.surface in textbox2[i]:
          npwordcount+=1
          negaposi,word=textbox2[i].split("\t")
          if "ポジ" in negaposi:pleasure+=0.3*wow
          elif "ネガ" in negaposi:pleasure+=-0.3*wow
          break
    for i in range(len(feeldic)): #感情辞書の判定
      if token.surface in feeldic[i]:
        feelwordcount+=1
        for i2 in range(len(feel)):feel[i2]+=wow*float(feeldic[i][i2+1])

  if npwordcount!=0:
    pleasure=pleasure/npwordcount
  if feelwordcount!=0:
    for i in range(len(feel)):feel[i]=feel[i]/feelwordcount
  return pleasure,feel

#ーーーここからは表示に関する記述なので、読まなくてよいーーー
textlist=[
"吾輩は猫である。名前はまだ無い。",
"恥の多い生涯を送って来ました。",
"メロスは激怒した。必ず、かの邪智暴虐の王を除かなければならぬと決意した。",
"そうか、そうか、つまりきみはそんなやつなんだな。",
"今日はステキな日だ。花が咲き、鳥が鳴いている。",
"レターパックで現金送れは全て詐欺です。",
]

for s in textlist:
  upleasure,ufeel=userfeeling(s)
  feeldic={0:"悲しみ",1:"恐怖",2:"怒り",3:"嫌悪",4:"信頼",5:"興奮",6:"喜び"}
  print("送信:",s)
  print("想定:",upleasure,ufeel)
  if upleasure==0:print("平常 且つ",end=" ")
  elif upleasure>0:print("ポジティブ 且つ",end=" ")
  elif upleasure<0:print("ネガティブ 且つ",end=" ")
  if (max(ufeel))>=1:howmatch="とても"
  elif (max(ufeel))>=0.6:howmatch="やや"
  elif (max(ufeel))>=0.3:howmatch="ほんのり"
  if max(ufeel)!=0:print(feeldic[ufeel.index(max(ufeel))]+"が"+howmatch+"強い文章です。",end="")
  else:print("無感情です。")
  ufeel[ufeel.index(max(ufeel))]=0
  if max(ufeel)!=0:print("次に"+feeldic[ufeel.index(max(ufeel))]+"が強いです。")
  else:print("")
  print("-------------------------")
