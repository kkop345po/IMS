from pathlib import Path
import re, html, json

p = Path('.agents/skills/bmad-brainstorming/assets/brain-selector.html')
s = p.read_text(encoding='utf-8')
rows = '''
肯定與延伸|不否定他人；每人先說「是的，而且……」，再延伸上一個點子，逐步累積彼此認同的新想法。
輪流書寫點子|大家先安靜寫下點子，再傳給下一位；每輪都接續眼前收到的內容繼續發想。
隨機刺激|隨機抽取一個詞語或圖像，強行連結到問題：這個東西能如何激發解法？
角色扮演|每個人代表不同的利害關係人，說出該角色的需求、擔憂，以及對點子的要求。
第一性原理思考|拆解所有假設，回到最基本的事實，再從這些事實重新建立解法。
逆向腦力激盪|先提出問題而非解法：如何讓這件事失敗？再逐一反轉，找出可行做法。
五個為什麼|連續追問五次「為什麼」，每次根據上一個答案往下挖，找出表象之下的根本原因。
挑釁式思考|刻意提出荒謬說法，再問：這能有什麼用？從中提煉可用的原理。
假設反轉|列出問題中隱含的每項假設，逐一反轉，再以相反的前提重新建立解法。
問題風暴|只提出問題，不准回答，直到真正值得解決的問題逐漸清晰。
因果迴路圖|畫出連結原因與結果的回饋迴路，找出強化與平衡循環，鎖定最能帶動改變的切入點。
形態分析法|列出問題中互相獨立的參數，為每項產生選項，再交叉組合，找出尚未嘗試的配置。
階梯式追問|不斷追問「這又能帶給你什麼？」，直到找到真正的深層需求，再針對該需求重新發想。
SCAMPER 奔馳法|從七個角度檢視點子：替代、結合、調整、修改、轉作他用、刪除、反轉。
六頂思考帽|依序從六個角度檢視問題：事實、感受、好處、風險、新點子、思考流程。
蓮花圖法|把主題放在九宮格中央，填入周圍八格，再將每格各自作為新九宮格的中心繼續延伸。
最糟點子法|刻意提出最差的解法，再反過來找出每個壞點子教會你的正確做法。
迪士尼創意法|讓點子輪流進入三個房間：夢想家（無所限制）、實踐家（如何實作）、批評家（哪裡會出問題）。
星爆法|只用誰、什麼、哪裡、何時、為什麼、如何來提問；各面向問透後再開始回答。
心智圖|從中心主題向外分支，每個節點再延伸子節點；跟隨聯想，讓想法網絡自由擴展。
瘋狂八點子|八分鐘內畫出八個點子，每格一個、不作修改，用速度超越內心的批判聲音。
我們可以如何|先將問題改寫成一組「我們可以如何……」的機會提問，再針對最精準的一題發想。
待完成任務|追問使用者真正想靠它完成什麼任務，再圍繞該任務發想，而非只關注原先假定的功能。
同理心地圖|整理使用者面對問題時說什麼、想什麼、做什麼、感受什麼，再從四個面向找出未被滿足的需求。
逆向推演|先具體描繪完成後的未來，再逐步往回推，找出現在必須先採取的第一步。
TRIZ 矛盾分析|指出核心矛盾：改善某件事卻會讓另一件事變差；再發想如何兩全其美，而不只是取捨。
魚骨圖|將問題主幹分成人員、流程、工具、環境等原因類別，再沿著每根魚骨挖掘成因。
放大成功經驗|指出目前哪些做法已經成功及其原因，再發想如何放大與延伸這些成果。
情境十字分析|選出兩項影響重大的不確定因素，交叉形成四種未來，再找出各種情境下都能奏效的行動。
決策樹分析|畫出每個決策點及其分岔路徑，沿各分支追蹤結果與風險。
解法矩陣|將問題變數與解決途徑排列成矩陣，為每格評分，尋找最佳搭配與尚未探索的空白。
特質移植|找出某個不相關成功案例的關鍵特質，再將這些特質移植到自己的問題上。
限制條件盤點|列出所有限制，區分真實限制與想像限制，再逐一設法消除、繞過，或轉化為優勢。
失敗分析|拆解一個相關的失敗案例：哪裡出錯、為何出錯、留下什麼教訓，以及如何運用在此處。
湧現思考|先不強求解法，觀察系統持續產生哪些模式，辨認其中正在自然形成的可能性。
假如情境|逐一移除限制：預算無上限、相反情況才是真的、問題已經消失；再追蹤由此出現的新可能。
類比思考|問「這像什麼？」，再借用對應領域的解題模式。
強制關聯|隨機挑選兩個無關的事物，強行建立連結，直到產生新點子。
時代轉換|先以二十世紀初工匠的身分解題，再以 2150 年殖民者的身分解題，提取不同時代的限制與巧思。
隱喻映射|將問題視為選定的隱喻，充分延伸，再把每個部分對應回原問題，尋找洞見。
跨界授粉|想像賭場、急診室、養蜂等截然不同的產業會如何解題，再調整其做法供自己使用。
概念融合|將兩個概念融合成全新的混合類別，說明融合後成了什麼，而不只是把兩者並列。
感官探索|從味道、氣味、聲音、觸感等感官檢視點子，找出理性分析以外的切入角度。
大自然的解法|找出已經解決類似問題的生物，再將其機制運用到設計中。
生態系思考|將問題畫成生態系：誰捕食誰、誰互相合作、什麼正在衰退，以及誰填補空缺。
演化壓力|產生大量粗糙變體，以嚴格規則篩選，再讓存活者衍生新版本，反覆迭代直到適應需求。
掠食者與獵物|挑選點子面臨的一項威脅，再設計動物可能演化出的防禦、偽裝或逃生機制。
變態發育階段|讓點子歷經卵、幼蟲、蛹、成體，每個生命階段都採用截然不同的形式與目的。
群體智慧|禁止中央總計畫，只讓個體遵循簡單的局部規則，使秩序由下而上自然形成。
原住民族智慧|指定一個原住民族或傳統知識體系，思考它會如何運用世代累積的智慧處理問題。
文化融合料理|挑選兩種不相關的文化，融合各自的處事方式，找出單一文化不會獨自產生的新做法。
儀式創新|將點子重新設計為儀式：定義進入儀式的門檻、動作，以及參與者經歷的轉變。
神話框架|將問題對應到神話：找出原型與相似故事，讓故事結構引導解決方式。
諺語採礦|蒐集不同文化中與主題有關的諺語，再以最挑戰既有假設的一句作為解法基礎。
祖先議會|邀請來自三種傳統的祖先或長者，分別評論你的點子，再調和彼此的分歧。
搗蛋鬼的計策|以郊狼、阿南西或洛基等詭計角色的視角，透過取巧、反轉或打破神聖規則來解題。
時間尺度階梯|分別針對一年、十年、一百年後設計解法，觀察哪些部分能延續、會失效或變得荒謬。
後稀缺測試|假設金錢、能源、時間或注意力等核心限制已無限且免費，點子將變成什麼樣子？
烏托邦與反烏托邦雙畫面|為同一個未來寫兩個版本：一切完美的宣傳文案，以及一切失控的新聞頭條。
來自未來的科幻物件|描述一件來自點子已經成功的世界中的實物、廣告或新聞片段，再逆向推導其形成方式。
新興科技碰撞|將點子與通用人工智慧、核融合、神經植入或基因編輯等前沿科技結合，看看會誕生什麼。
世界變局翻牌|抽取一項劇烈世界變局，例如沒有隱私、人口減半、壽命兩百歲，再重新設計點子以適應它。
未來人類學考古|想像 2200 年的學者挖出你的點子作為遺物：它透露了我們什麼？後來又被什麼取代？
觀察者效應|思考觀察、測量或推出點子的行為，如何改變你原本想掌握的事物。
糾纏思考|將問題中相距甚遠的兩個部分配對，假定一方改變就立刻牽動另一方，找出隱藏連結。
疊加態坍縮|暫時保留所有互相競爭的解法，再找出能讓它們收斂成唯一贏家的關鍵限制。
相對性視角轉換|從操作緩慢的使用者、競爭對手或未來的自己等截然不同的視角重看點子，觀察哪些事會改觀。
力場線|將目標視為電荷，畫出推動各方靠近或遠離目標的無形力量。
量子穿隧|假設點子能直接穿過「不可能」的障礙，無須翻越；另一側有什麼，又如何低成本抵達？
混沌工程|刻意用各種方式讓點子失敗，再只以經得起破壞的部分重新建立方案。
游擊播種|將解法種在最意想不到的地方，讓它悄悄成長，直到令所有人驚豔。
海盜法則腦力激盪|從各處借取最好的部分，大膽重新組合，抓住有用的做法就向前行。
殭屍末日規劃|社會剛剛崩潰；將點子精簡到在沒電、沒有規則、沒有後援時仍能存活的部分。
微醺歷史重述|像喝了三杯後那樣解釋它：不修飾、不用術語，只說最直接、最簡單的真相。
反解法|發想如何把問題弄得極度糟糕，再將每種破壞手法反轉成解法。
四大元素|讓火、水、土、風各自以猛烈的方式重塑點子，看看最後留下什麼。
反派獨白|以邪惡主謀炫耀陰謀的口吻描述問題，讓這個邪惡計畫揭露真正的解法。
向黃金獵犬解說|向一隻只在乎零食、球和睡覺的興奮狗狗推介點子，只保留牠能理解的核心。
凌晨三點購物廣告|把尚未成熟的點子當成深夜購物廣告推銷，不斷喊「等等，還有！」，直到想出更多功能。
感恩節的醉酒叔叔|讓最吵、最直言不諱的親戚抱怨問題，從誇張評論中挖掘隱藏的真相。
惡意精靈|許下一個願望，讓惡意精靈以字面正確卻災難性的方式實現它，再逐一補上漏洞。
三輪荒唐點子|第一輪提出荒謬點子，第二輪讓每個點子更荒謬，第三輪從最可笑的內容中找出最小的認真想法。
時光旅行脫口秀|主持一場訪談，邀請過去、現在與未來的自己，從各時期挖掘解題建議。
外星人類學家|化身困惑的外星人研究問題，大聲說出其中哪些事情顯得奇怪、武斷或不可理喻。
夢想融合實驗室|先說出不可能的夢幻解法，再逆向推導連回現實所需的步驟。
情緒交響樂團|分別由憤怒、喜悅、恐懼、希望等情緒主導一輪發想，再協調彼此衝突的點子。
平行宇宙咖啡館|改寫一項現實的基本規則，例如物理、經濟或社會規範，再依新法則解決問題。
角色旅程|化身某個典型角色，以該角色的身分解題，指出它看見了哪些你平常忽略的事。
魔鬼代言人法庭|模擬審判：起訴點子、為點子辯護，再由陪審團宣判，每個角色都完整陳述立場。
捨棄皇冠上的寶石|刪除最好、最受喜愛的那項功能，再重新設計整個方案，使它缺少此功能仍能成功。
千倍預算|假設金錢、時間與人力無限，先設計誇張版本，再從中挑出實際可採用的點子。
六十分鐘內推出|一小時後就要用現有資源推出成果；指出必須刪除、暫時模擬或借用哪些部分。
零元任務|完全不花錢達成目標：不買工具、不聘人、不投廣告，只靠人脈、互助與現有資源。
只能留一項功能|只能保留一項能力；選出它，再將這唯一的功能做到極致。
把旋鈕轉到十一|選定一個面向並誇張到極致：最快、最大、最便宜或最古怪，看看會突破什麼。
限制輪盤|每輪隨機抽取嚴苛限制，例如沒有螢幕、團隊減半、只剩一天；重新解題，留下經得起考驗的點子。
內在小孩會議|以七歲的自己回答，不斷天真追問「為什麼」，追逐好奇，暫時禁止無聊的大人想法。
陰影探索|指出自己對此逃避、抗拒或害怕的事情，再深入挖掘其中隱藏的洞見。
價值觀考古|不斷追問「我為什麼在乎？」，直到找出默默主導選擇、不可妥協的核心價值。
訪談未來的自己|訪問八十歲、充滿智慧的自己，記下對方給這個問題的建議。
身體智慧對話|留意每個選項引發的緊繃、悸動或直覺牽引，讓身體的肯定與否定帶動發想。
給自己許可|明確寫下允許自己思考禁忌或不可能想法的許可，再大聲說出那個想法。
秘密願望告白|說出自己在此偷偷渴望卻不好意思承認的事情，再設計一個尊重該願望的點子。
心情氣象報告|指出此刻內心是霧、風暴或晴天，讓這個真實的情緒氣候帶動發想。
點子接力賽|每人三十秒、不能停頓：補上一個點子立刻交棒，在任何人想太多之前持續往前。
點子燙手山芋|讓同一個點子在圈內傳遞，每個接手者必須在十秒內改造它再傳出，而且不能重複。
借用再升級|挑選旁人一個讓你羨慕的點子，公開借用，明確改進後再交還。
摺紙接龍|每人只看前一小段，為隱藏的圖畫或句子增添一筆，最後展開超現實的完整成果。
'''.strip().splitlines()
cards = list(dict.fromkeys(re.findall(r'data-name="([^"]+)" data-cat="[^"]+" data-desc="([^"]+)"', s)))
assert len(cards) == len(rows), (len(cards),len(rows))
mapping = {}
for (name, desc), row in zip(cards, rows):
    n, d = row.split('|')
    mapping[html.unescape(name)] = n
    mapping[html.unescape(desc)] = d
cats = dict(zip(['Proven & Professional','Structured','Deep','Creative','Biomimetic','Cultural','Speculative Future','Quantum','Wild','Absurdist','Theatrical','Constraint','Introspective Delight','Collaborative','Introspective & Personal'], ['經典專業方法','結構化思考','深度探索','創意發想','仿生靈感','文化啟發','未來想像','量子隱喻','狂野發想','荒誕創意','戲劇演繹','限制挑戰','內省探索','協作共創','內省與個人成長']))
mapping.update(cats)
mapping.update(dict(zip(['Build a feature','Novel concept','Strategy','Planning','Diagnose','Personal / life','Get unstuck'],['開發功能','新穎概念','策略','規劃','問題診斷','個人／生活','突破卡關'])))
for cat, zh in cats.items():
    mapping['✨ Invent a '+cat+' technique'] = '✨ 自創「'+zh+'」技巧'
    mapping['Make up a brand-new technique on the fly, in the spirit of '+cat] = '依照「'+zh+'」的精神，即興創造一種全新的技巧。'
mapping.update({'BMad Method Brainstorming Selection':'BMad Method 腦力激盪技巧選擇器','Facilitation':'引導方式','Facilitator':'引導者','Creative Partner':'創意夥伴','Ideate for me':'替我發想','Techniques':'發想技巧','Picked ':'已選 ','Random ':'隨機 ','Invent ':'自創 ','AI picks ':'AI 挑選 ','Copy prompt':'複製提示詞','Great for':'適用目標','Jump to':'跳至分類','BMad Method · Brainstorming':'BMad Method · 腦力激盪','Total 0 · 3–4 is the sweet spot':'共 0 項 · 建議選擇 3–4 項','✓ Copied! Now paste it into the chat to start your session.':'✓ 已複製！請貼回聊天室，開始腦力激盪。','Compose your session, hit ':'設定你的腦力激盪活動，按下 ',' ,':''})
mapping.pop(' ,')
mapping['Compose your session, hit '] = '設定你的腦力激盪活動，按下 '
mapping[', and paste it back into the chat to begin. 108 techniques across 13 categories.'] = '，再貼回聊天室即可開始。共 13 類、108 種技巧。'
def text_node(m):
    raw=m.group(1); value=html.unescape(raw)
    if value.startswith('Great for: '):
        value='適用目標：'+ ' · '.join(mapping.get(x,x) for x in value[11:].split(' · '))
    else: value=mapping.get(value,value)
    return '>'+html.escape(value,quote=False)+'<' if value != html.unescape(raw) else m.group(0)
# Translate markup text only, leaving scripts, SVGs and machine identifiers intact.
parts=re.split(r'(<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>)',s,flags=re.S)
for i in range(0,len(parts),2): parts[i]=re.sub(r'>([^<>]+)<',text_node,parts[i])
s=''.join(parts).replace('<html lang="en">','<html lang="zh-Hant">')
s=s.replace('Toggle dark mode','切換深色模式')
replacements={
'A forcing function for your ideas — I prompt and push, but never supply them.':'透過提問與挑戰激發你的想法，由你提出點子。',
'We riff together — I facilitate and add ideas too, each logged as yours or mine.':'我們一起激盪創意；我負責引導並提出點子，分別標記你的與我的想法。',
'I run the whole session myself, then show you the result and offer to keep going.':'由我完成整場發想，再展示成果，並詢問你是否繼續。',
"'Total ' + total + ' · 3–4 is the sweet spot'":"'共 ' + total + ' 項 · 建議選擇 3–4 項'",
'✓ Copied! Now paste it into the chat to start your session.':'✓ 已複製！請貼回聊天室，開始腦力激盪。',
'⚠ Couldn’t reach the clipboard — copy the text in the box, then paste it into the chat.':'⚠ 無法存取剪貼簿，請複製對話框中的文字，再貼回聊天室。',
'Copy this, then paste it into the chat:':'請複製以下文字，再貼回聊天室：',
'"Let\'s run my brainstorming session."':'"請開始我的腦力激盪活動，並全程使用繁體中文。"',
"'Facilitation mode: ' + state.mode + '.'":"'引導模式：' + tr(state.mode) + '。'",
'Techniques to use:':'使用以下技巧：',
' (random pick)':'（隨機挑選）',
"' ' + t.n + '  ·  ' + t.c":"' ' + tr(t.n) + '  ·  ' + tr(t.c) + ' [' + t.n + ']'",
"'   ' + t.d":"'   ' + tr(t.d)",
"'invent ' + state.inv + ' brand-new technique' + (state.inv > 1 ? 's' : '') + ' on the fly'":"'即興自創 ' + state.inv + ' 種全新技巧'",
"'invent 1 new technique in the spirit of ' + b.dataset.invent":"'依照「' + tr(b.dataset.invent) + '」的精神自創 1 種技巧'",
"'you choose ' + state.ai + ' more technique' + (state.ai > 1 ? 's' : '') + ' that fit my goal'":"'請再挑選 ' + state.ai + ' 種符合我目標的技巧'",
"'Then: ' + extra.join('; and ') + '.'":"'接著：' + extra.join('；並且') + '。'",
'Run the whole session yourself — pick the techniques, generate the ideas, then show me the result.':'請自行完成整場活動：挑選技巧、產生點子，再展示成果。',
'Help me choose 3–4 techniques to start.':'請先協助我挑選 3–4 種技巧。'
}
for a,b in replacements.items():
    assert a in s, a
    s=s.replace(a,b)
inject='var ZH = '+json.dumps(mapping,ensure_ascii=False)+';\n  function tr(s){ return ZH[s] || s; }\n  '
s=s.replace("var $ = function(id)",inject+"var $ = function(id)")
out=Path('brain-selector.zh-TW.html')
out.write_text(s,encoding='utf-8')
print('Translated',len(cards),'unique techniques;',len(mapping),'translation entries. Output:',out)
