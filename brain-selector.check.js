
/* set the theme before first paint so there's no light-mode flash */
(function(){ try {
  var t = localStorage.getItem('bmad-theme');
  if (!t) { t = (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light'; }
  document.documentElement.setAttribute('data-theme', t);
} catch(e){} })();


(function(){
  var ZH = {"Yes And Building": "肯定與延伸", "Never negate; each person opens with \"Yes, and...\" and adds to the last idea, stacking a chain of accepted additions": "不否定他人；每人先說「是的，而且……」，再延伸上一個點子，逐步累積彼此認同的新想法。", "Brain Writing Round Robin": "輪流書寫點子", "Everyone writes ideas silently, then passes their sheet; you build on whatever lands in front of you, round after round": "大家先安靜寫下點子，再傳給下一位；每輪都接續眼前收到的內容繼續發想。", "Random Stimulation": "隨機刺激", "Pull a random word or image and force a link to the problem: \"how does THIS spark a solution?\"": "隨機抽取一個詞語或圖像，強行連結到問題：這個東西能如何激發解法？", "Role Playing": "角色扮演", "Each person speaks as a different stakeholder, voicing what that role wants, fears, and would demand of the idea": "每個人代表不同的利害關係人，說出該角色的需求、擔憂，以及對點子的要求。", "First Principles Thinking": "第一性原理思考", "Strip every assumption to bedrock facts, then rebuild the solution from scratch on truth alone": "拆解所有假設，回到最基本的事實，再從這些事實重新建立解法。", "Reverse Brainstorming": "逆向腦力激盪", "Generate problems instead of solutions — 'how could we make this fail?' — then mine each for its inverse": "先提出問題而非解法：如何讓這件事失敗？再逐一反轉，找出可行做法。", "Five Whys": "五個為什麼", "Ask \"why?\" five times in a chain, each answer feeding the next, until you hit the root cause beneath the symptom": "連續追問五次「為什麼」，每次根據上一個答案往下挖，找出表象之下的根本原因。", "Provocation Technique": "挑釁式思考", "State something deliberately absurd, then mine it: \"how could this be useful?\" Extract the usable principle hiding inside": "刻意提出荒謬說法，再問：這能有什麼用？從中提煉可用的原理。", "Assumption Reversal": "假設反轉", "List every assumption baked into the problem, flip each to its opposite, then rebuild a solution on the inverted foundation": "列出問題中隱含的每項假設，逐一反轉，再以相反的前提重新建立解法。", "Question Storming": "問題風暴", "Generate only questions about the problem, zero answers allowed, until the real problem worth solving comes into focus": "只提出問題，不准回答，直到真正值得解決的問題逐漸清晰。", "Causal Loop Mapping": "因果迴路圖", "Diagram the feedback loops linking causes and effects, find the reinforcing and balancing cycles, and target the leverage point": "畫出連結原因與結果的回饋迴路，找出強化與平衡循環，鎖定最能帶動改變的切入點。", "Morphological Analysis": "形態分析法", "List the problem's independent parameters, generate options for each, then combine across them to surface untried configurations": "列出問題中互相獨立的參數，為每項產生選項，再交叉組合，找出尚未嘗試的配置。", "Laddering": "階梯式追問", "Ask 'and what would that give you?' up the chain until you reach the real underlying need, then ideate fresh at that level": "不斷追問「這又能帶給你什麼？」，直到找到真正的深層需求，再針對該需求重新發想。", "SCAMPER Method": "SCAMPER 奔馳法", "Run your idea through seven lenses: Substitute, Combine, Adapt, Modify, Put-to-other-use, Eliminate, Reverse": "從七個角度檢視點子：替代、結合、調整、修改、轉作他用、刪除、反轉。", "Six Thinking Hats": "六頂思考帽", "Examine the problem six ways one at a time: facts, feelings, benefits, risks, new ideas, process": "依序從六個角度檢視問題：事實、感受、好處、風險、新點子、思考流程。", "Lotus Blossom": "蓮花圖法", "Put the theme at the center of a 3x3 grid, fill the 8 cells around it, then promote each of those to the center of its own new 3x3": "把主題放在九宮格中央，填入周圍八格，再將每格各自作為新九宮格的中心繼續延伸。", "Worst Possible Idea": "最糟點子法", "Deliberately generate the most terrible solutions you can, then flip each into what it teaches you to do right": "刻意提出最差的解法，再反過來找出每個壞點子教會你的正確做法。", "Disney Method": "迪士尼創意法", "Cycle the idea through three rooms: Dreamer (anything goes), Realist (how we'd build it), Critic (what breaks)": "讓點子輪流進入三個房間：夢想家（無所限制）、實踐家（如何實作）、批評家（哪裡會出問題）。", "Starbursting": "星爆法", "Interrogate the idea with only questions — who, what, where, when, why, how — exhaust each before answering any": "只用誰、什麼、哪裡、何時、為什麼、如何來提問；各面向問透後再開始回答。", "Mind Mapping": "心智圖", "Branch the central topic outward, each node spawning children; follow tangents wherever they pull and let the web sprawl": "從中心主題向外分支，每個節點再延伸子節點；跟隨聯想，讓想法網絡自由擴展。", "Crazy 8s": "瘋狂八點子", "Eight ideas in eight minutes, one per box, no editing — speed outruns your inner critic": "八分鐘內畫出八個點子，每格一個、不作修改，用速度超越內心的批判聲音。", "How Might We": "我們可以如何", "Reframe the problem as a batch of 'How might we...' opportunity questions first, then ideate against the sharpest one": "先將問題改寫成一組「我們可以如何……」的機會提問，再針對最精準的一題發想。", "Job to Be Done": "待完成任務", "Ask what the user is really hiring this to do, then ideate around that underlying job, not the feature you assumed": "追問使用者真正想靠它完成什麼任務，再圍繞該任務發想，而非只關注原先假定的功能。", "Empathy Map": "同理心地圖", "Map what the user says, thinks, does, and feels around the problem, then mine each quadrant for the unmet need": "整理使用者面對問題時說什麼、想什麼、做什麼、感受什麼，再從四個面向找出未被滿足的需求。", "Backcasting": "逆向推演", "Fix the finished future in vivid detail, then work backward step by step to the one move you'd have to make first": "先具體描繪完成後的未來，再逐步往回推，找出現在必須先採取的第一步。", "TRIZ Contradiction": "TRIZ 矛盾分析", "Name the core contradiction (what only improves by making something else worse), then brainstorm ways to win both instead of trading off": "指出核心矛盾：改善某件事卻會讓另一件事變差；再發想如何兩全其美，而不只是取捨。", "Fishbone Diagram": "魚骨圖", "Branch the problem's spine into cause categories (people, process, tools, environment) and mine each bone for contributing causes": "將問題主幹分成人員、流程、工具、環境等原因類別，再沿著每根魚骨挖掘成因。", "Build on What Works": "放大成功經驗", "Name what's already succeeding and why, then ideate how to amplify and extend it instead of fixing what's broken": "指出目前哪些做法已經成功及其原因，再發想如何放大與延伸這些成果。", "Scenario Cross": "情境十字分析", "Pick two high-impact uncertainties, cross them into four futures, and ideate the move that wins in every one": "選出兩項影響重大的不確定因素，交叉形成四種未來，再找出各種情境下都能奏效的行動。", "Decision Tree Mapping": "決策樹分析", "Chart every choice point and the paths it forks into, following each branch to its outcome and risk": "畫出每個決策點及其分岔路徑，沿各分支追蹤結果與風險。", "Solution Matrix": "解法矩陣", "Grid problem variables against solution approaches, score every cell, hunt the best pairings and empty gaps": "將問題變數與解決途徑排列成矩陣，為每格評分，尋找最佳搭配與尚未探索的空白。", "Trait Transfer": "特質移植", "Name what makes an unrelated success work, then graft those winning traits onto your own problem": "找出某個不相關成功案例的關鍵特質，再將這些特質移植到自己的問題上。", "Constraint Mapping": "限制條件盤點", "Map every constraint, sort real from imagined, then attack each: dissolve it, route around it, or turn it into an asset": "列出所有限制，區分真實限制與想像限制，再逐一設法消除、繞過，或轉化為優勢。", "Failure Analysis": "失敗分析", "Dissect a relevant failure: what broke, why it broke, what lesson it leaves, and how to apply that wisdom here": "拆解一個相關的失敗案例：哪裡出錯、為何出錯、留下什麼教訓，以及如何運用在此處。", "Emergent Thinking": "湧現思考", "Stop forcing a solution; watch what patterns the system keeps producing and name what's trying to emerge on its own": "先不強求解法，觀察系統持續產生哪些模式，辨認其中正在自然形成的可能性。", "What If Scenarios": "假如情境", "Detonate one constraint at a time — unlimited budget, opposite is true, problem vanished — and chase what rushes in": "逐一移除限制：預算無上限、相反情況才是真的、問題已經消失；再追蹤由此出現的新可能。", "Analogical Thinking": "類比思考", "Ask 'this is like what?' and steal the solution pattern from the domain that answers": "問「這像什麼？」，再借用對應領域的解題模式。", "Forced Relationships": "強制關聯", "Grab two unrelated things at random and force a bridge between them until an idea falls out": "隨機挑選兩個無關的事物，強行建立連結，直到產生新點子。", "Time Shifting": "時代轉換", "Solve the problem as a 1900s artisan, then a 2150 colonist — harvest the era-bound constraints and tricks": "先以二十世紀初工匠的身分解題，再以 2150 年殖民者的身分解題，提取不同時代的限制與巧思。", "Metaphor Mapping": "隱喻映射", "Declare the problem IS a chosen metaphor, extend the metaphor fully, map each part back to find insights": "將問題視為選定的隱喻，充分延伸，再把每個部分對應回原問題，尋找洞見。", "Cross-Pollination": "跨界授粉", "Ask how a wildly different industry — casinos, ERs, beekeeping — would crack this, then adapt their move": "想像賭場、急診室、養蜂等截然不同的產業會如何解題，再調整其做法供自己使用。", "Concept Blending": "概念融合", "Fuse two concepts into one new hybrid category and name what the merger becomes, not just combines": "將兩個概念融合成全新的混合類別，說明融合後成了什麼，而不只是把兩者並列。", "Sensory Exploration": "感官探索", "Interrogate the idea through each sense — its taste, smell, sound, texture — to surface non-analytical angles": "從味道、氣味、聲音、觸感等感官檢視點子，找出理性分析以外的切入角度。", "Nature's Solutions": "大自然的解法", "Name an organism that already solved your problem, then copy its mechanism into your design": "找出已經解決類似問題的生物，再將其機制運用到設計中。", "Ecosystem Thinking": "生態系思考", "Map your problem as an ecosystem: who eats whom, who partners, what decays, what fills the gaps": "將問題畫成生態系：誰捕食誰、誰互相合作、什麼正在衰退，以及誰填補空缺。", "Evolutionary Pressure": "演化壓力", "Spawn many ugly variants, apply a brutal selection rule, breed the survivors, repeat until it adapts": "產生大量粗糙變體，以嚴格規則篩選，再讓存活者衍生新版本，反覆迭代直到適應需求。", "Predator & Prey": "掠食者與獵物", "Pick a threat to your idea, then design the defense, camouflage, or escape an animal would evolve against it": "挑選點子面臨的一項威脅，再設計動物可能演化出的防禦、偽裝或逃生機制。", "Metamorphosis Stages": "變態發育階段", "Force your idea through egg, larva, pupa, adult: a radically different form and purpose at each life stage": "讓點子歷經卵、幼蟲、蛹、成體，每個生命階段都採用截然不同的形式與目的。", "Swarm Logic": "群體智慧", "Forbid the master plan: solve it with dumb local rules each agent follows so order emerges from the bottom up": "禁止中央總計畫，只讓個體遵循簡單的局部規則，使秩序由下而上自然形成。", "Indigenous Wisdom": "原住民族智慧", "Ask how an indigenous or traditional knowledge system would approach this — name the culture, channel its ancestral problem-solving": "指定一個原住民族或傳統知識體系，思考它會如何運用世代累積的智慧處理問題。", "Fusion Cuisine": "文化融合料理", "Pick two unrelated cultures and force-blend their approaches; harvest the hybrid that neither alone would invent": "挑選兩種不相關的文化，融合各自的處事方式，找出單一文化不會獨自產生的新做法。", "Ritual Innovation": "儀式創新", "Redesign the idea as a ceremony — define the threshold, the gestures, the transformation participants undergo": "將點子重新設計為儀式：定義進入儀式的門檻、動作，以及參與者經歷的轉變。", "Mythic Frameworks": "神話框架", "Map the problem onto a myth: name the archetypes, find the parallel tale, let its structure dictate the resolution": "將問題對應到神話：找出原型與相似故事，讓故事結構引導解決方式。", "Proverb Mining": "諺語採礦", "Collect proverbs from many cultures on this theme, then build the solution from the one that clashes hardest with your assumptions": "蒐集不同文化中與主題有關的諺語，再以最挑戰既有假設的一句作為解法基礎。", "Ancestor Council": "祖先議會", "Convene three ancestors or elders from different traditions, voice each one's verdict on your idea, reconcile their disagreement": "邀請來自三種傳統的祖先或長者，分別評論你的點子，再調和彼此的分歧。", "Trickster's Gambit": "搗蛋鬼的計策", "Channel the trickster figure — coyote, Anansi, Loki — and solve it by cheating, inverting, or breaking the sacred rule": "以郊狼、阿南西或洛基等詭計角色的視角，透過取巧、反轉或打破神聖規則來解題。", "Time Horizon Ladder": "時間尺度階梯", "Solve the idea for 1 year out, then 10, then 100 — note what survives, breaks, or becomes absurd at each rung": "分別針對一年、十年、一百年後設計解法，觀察哪些部分能延續、會失效或變得荒謬。", "Post-Scarcity Test": "後稀缺測試", "Assume the core constraint (money, energy, time, attention) is now infinite and free — what does the idea become": "假設金錢、能源、時間或注意力等核心限制已無限且免費，點子將變成什麼樣子？", "Utopia vs Dystopia Split-Screen": "烏托邦與反烏托邦雙畫面", "Write the same future twice: the brochure where it went perfectly and the headline where it went horribly": "為同一個未來寫兩個版本：一切完美的宣傳文案，以及一切失控的新聞頭條。", "Sci-Fi Artifact From the Future": "來自未來的科幻物件", "Describe one physical object, ad, or news clip from the world where this idea already won — reverse-engineer it": "描述一件來自點子已經成功的世界中的實物、廣告或新聞片段，再逆向推導其形成方式。", "Emerging Tech Collision": "新興科技碰撞", "Force-marry your idea to a frontier tech (AGI, fusion, neural implants, gene edit) and ask what new thing is born": "將點子與通用人工智慧、核融合、神經植入或基因編輯等前沿科技結合，看看會誕生什麼。", "What-If-The-World-Changed Card Flip": "世界變局翻牌", "Draw a wild world-shift (no privacy, half population, 200-yr lifespans) and redesign the idea to fit that world": "抽取一項劇烈世界變局，例如沒有隱私、人口減半、壽命兩百歲，再重新設計點子以適應它。", "Future Anthropologist Dig": "未來人類學考古", "A scholar in 2200 unearths your idea as a relic — what do they conclude it reveals about us, and what replaced it": "想像 2200 年的學者挖出你的點子作為遺物：它透露了我們什麼？後來又被什麼取代？", "Observer Effect": "觀察者效應", "Ask how the act of watching, measuring, or shipping this idea changes the very thing you're trying to capture": "思考觀察、測量或推出點子的行為，如何改變你原本想掌握的事物。", "Entanglement Thinking": "糾纏思考", "Pair two distant parts of the problem and insist a change in one instantly flips the other — surface the hidden linkage": "將問題中相距甚遠的兩個部分配對，假定一方改變就立刻牽動另一方，找出隱藏連結。", "Superposition Collapse": "疊加態坍縮", "Hold all rival solutions alive at once, then name the one constraint that collapses them to a single winner": "暫時保留所有互相競爭的解法，再找出能讓它們收斂成唯一贏家的關鍵限制。", "Relativity Frame Shift": "相對性視角轉換", "Re-run the idea from a wildly different observer's reference frame — the slow user, the rival, future-you — and see what warps": "從操作緩慢的使用者、競爭對手或未來的自己等截然不同的視角重看點子，觀察哪些事會改觀。", "Field Lines": "力場線", "Treat the goal as a charge and map the invisible forces pulling every stakeholder toward or away from it": "將目標視為電荷，畫出推動各方靠近或遠離目標的無形力量。", "Quantum Tunneling": "量子穿隧", "Assume the idea can pass straight through the 'impossible' barrier instead of over it — what's on the other side, reached cheaply": "假設點子能直接穿過「不可能」的障礙，無須翻越；另一側有什麼，又如何低成本抵達？", "Chaos Engineering": "混沌工程", "Deliberately break your idea every way it could fail, then rebuild only the parts that survive the wreckage": "刻意用各種方式讓點子失敗，再只以經得起破壞的部分重新建立方案。", "Guerrilla Gardening Ideas": "游擊播種", "Plant your solution in the least expected place and let it grow underground until it surprises everyone": "將解法種在最意想不到的地方，讓它悄悄成長，直到令所有人驚豔。", "Pirate Code Brainstorm": "海盜法則腦力激盪", "Steal the best bits from anywhere, remix without asking permission, grab what works and run": "從各處借取最好的部分，大膽重新組合，抓住有用的做法就向前行。", "Zombie Apocalypse Planning": "殭屍末日規劃", "Society just collapsed — strip your idea to only what survives with no power, no rules, no backup": "社會剛剛崩潰；將點子精簡到在沒電、沒有規則、沒有後援時仍能存活的部分。", "Drunk History Retelling": "微醺歷史重述", "Explain it like you're three drinks in: no filter, no jargon, just the raw stupid-simple truth": "像喝了三杯後那樣解釋它：不修飾、不用術語，只說最直接、最簡單的真相。", "Anti-Solution": "反解法", "Brainstorm how to make the problem spectacularly worse, then invert every sabotage into a fix": "發想如何把問題弄得極度糟糕，再將每種破壞手法反轉成解法。", "Elemental Forces": "四大元素", "Let fire, water, earth, and air each sculpt your idea their own brutal way and see what survives": "讓火、水、土、風各自以猛烈的方式重塑點子，看看最後留下什麼。", "Villain's Monologue": "反派獨白", "Pitch your problem as an evil mastermind gloating about their scheme; the diabolical plan reveals the real solution": "以邪惡主謀炫耀陰謀的口吻描述問題，讓這個邪惡計畫揭露真正的解法。", "Explain It to a Golden Retriever": "向黃金獵犬解說", "Re-pitch the idea to an excitable dog who only cares about treats, balls, and naps; keep only what survives": "向一隻只在乎零食、球和睡覺的興奮狗狗推介點子，只保留牠能理解的核心。", "Infomercial at 3AM": "凌晨三點購物廣告", "Sell your half-baked idea as a desperate late-night infomercial: 'But wait, there's more!' until features fall out": "把尚未成熟的點子當成深夜購物廣告推銷，不斷喊「等等，還有！」，直到想出更多功能。", "Drunk Uncle at Thanksgiving": "感恩節的醉酒叔叔", "Have your loudest, least-filtered relative rant about the problem; mine the unhinged hot takes for buried truth": "讓最吵、最直言不諱的親戚抱怨問題，從誇張評論中挖掘隱藏的真相。", "Cursed Genie": "惡意精靈", "Make a wish, then let a malicious genie grant it in the most technically-correct disastrous way; patch each loophole": "許下一個願望，讓惡意精靈以字面正確卻災難性的方式實現它，再逐一補上漏洞。", "Three Rounds of Stupid": "三輪荒唐點子", "Round 1 absurd ideas, Round 2 make each MORE absurd, Round 3 find the smallest serious thing hiding in the silliest": "第一輪提出荒謬點子，第二輪讓每個點子更荒謬，第三輪從最可笑的內容中找出最小的認真想法。", "Time Travel Talk Show": "時光旅行脫口秀", "Host a talk show interviewing your past, present, and future selves to mine each era for advice on the problem": "主持一場訪談，邀請過去、現在與未來的自己，從各時期挖掘解題建議。", "Alien Anthropologist": "外星人類學家", "Become a baffled alien studying the problem and narrate aloud what seems strange, arbitrary, or insane about it": "化身困惑的外星人研究問題，大聲說出其中哪些事情顯得奇怪、武斷或不可理喻。", "Dream Fusion Laboratory": "夢想融合實驗室", "Voice the impossible fantasy solution first, then reverse-engineer the bridging steps back to reality": "先說出不可能的夢幻解法，再逆向推導連回現實所需的步驟。", "Emotion Orchestra": "情緒交響樂團", "Run a separate ideation round led by each emotion (rage, joy, fear, hope), then harmonize their conflicting ideas": "分別由憤怒、喜悅、恐懼、希望等情緒主導一輪發想，再協調彼此衝突的點子。", "Parallel Universe Cafe": "平行宇宙咖啡館", "Rewrite one fundamental rule of reality (physics, economics, social norms) and solve the problem under those laws": "改寫一項現實的基本規則，例如物理、經濟或社會規範，再依新法則解決問題。", "Persona Journey": "角色旅程", "Embody an archetype and solve the problem in-character, naming what that persona sees that you normally miss": "化身某個典型角色，以該角色的身分解題，指出它看見了哪些你平常忽略的事。", "Devil's Advocate Courtroom": "魔鬼代言人法庭", "Stage a trial: prosecute the idea, defend it, then deliver the jury verdict, each role argued fully in character": "模擬審判：起訴點子、為點子辯護，再由陪審團宣判，每個角色都完整陳述立場。", "Kill the Crown Jewel": "捨棄皇冠上的寶石", "Delete the single best, most beloved feature — now redesign the whole thing to win without it": "刪除最好、最受喜愛的那項功能，再重新設計整個方案，使它缺少此功能仍能成功。", "1000x Budget": "千倍預算", "Pretend money, time, and people are infinite — design the absurd version, then mine it for ideas you can actually steal": "假設金錢、時間與人力無限，先設計誇張版本，再從中挑出實際可採用的點子。", "Ship in 60 Minutes": "六十分鐘內推出", "You launch in one hour with what's already on hand — name what you cut, fake, or borrow to make it real": "一小時後就要用現有資源推出成果；指出必須刪除、暫時模擬或借用哪些部分。", "The $0 Mandate": "零元任務", "Achieve the goal spending literally nothing — no tools, hires, or ads; only people, favors, and what you own": "完全不花錢達成目標：不買工具、不聘人、不投廣告，只靠人脈、互助與現有資源。", "One Feature Only": "只能留一項功能", "You may keep exactly ONE capability and nothing else — pick it, then make that single thing unbelievably good": "只能保留一項能力；選出它，再將這唯一的功能做到極致。", "Crank the Dial to 11": "把旋鈕轉到十一", "Pick one dimension and exaggerate it to a ludicrous extreme — fastest, biggest, cheapest, weirdest — and see what breaks open": "選定一個面向並誇張到極致：最快、最大、最便宜或最古怪，看看會突破什麼。", "Constraint Roulette": "限制輪盤", "Each round draw a brutal random limit (no screens, half the team, one day) and re-solve under it; survivors become real ideas": "每輪隨機抽取嚴苛限制，例如沒有螢幕、團隊減半、只剩一天；重新解題，留下經得起考驗的點子。", "Inner Child Conference": "內在小孩會議", "Answer as your 7-year-old self: ask naive 'why why why' questions, chase wonder, ban every boring adult thought": "以七歲的自己回答，不斷天真追問「為什麼」，追逐好奇，暫時禁止無聊的大人想法。", "Shadow Work Mining": "陰影探索", "Name what you're avoiding, resisting, or scared of about this — then dig there for the buried insight": "指出自己對此逃避、抗拒或害怕的事情，再深入挖掘其中隱藏的洞見。", "Values Archaeology": "價值觀考古", "Keep asking 'why do I care?' until you hit bedrock: the non-negotiable value secretly steering the choice": "不斷追問「我為什麼在乎？」，直到找出默默主導選擇、不可妥協的核心價值。", "Future Self Interview": "訪談未來的自己", "Interview your wise 80-year-old self about this problem and write down the advice they give you": "訪問八十歲、充滿智慧的自己，記下對方給這個問題的建議。", "Body Wisdom Dialogue": "身體智慧對話", "Scan for the tension, flutter, or gut pull each option triggers; let the body's yes/no drive the ideas": "留意每個選項引發的緊繃、悸動或直覺牽引，讓身體的肯定與否定帶動發想。", "Permission Giving": "給自己許可", "Write yourself an explicit permission slip to think the forbidden, impossible thought — then think it out loud": "明確寫下允許自己思考禁忌或不可能想法的許可，再大聲說出那個想法。", "Secret Wish Confession": "秘密願望告白", "Whisper the embarrassing thing you secretly want here but won't admit, then build the idea honoring it": "說出自己在此偷偷渴望卻不好意思承認的事情，再設計一個尊重該願望的點子。", "Mood Weather Report": "心情氣象報告", "Name the inner weather right now (fog, storm, sun) and let that exact emotional climate generate the ideas": "指出此刻內心是霧、風暴或晴天，讓這個真實的情緒氣候帶動發想。", "Ideation Relay Race": "點子接力賽", "30-second turns, no pausing: add one idea, slap it to the next person, keep the baton moving before anyone overthinks": "每人三十秒、不能停頓：補上一個點子立刻交棒，在任何人想太多之前持續往前。", "Idea Hot Potato": "點子燙手山芋", "One idea gets tossed around the circle; each catcher must mutate it in 10 seconds before passing, no repeats allowed": "讓同一個點子在圈內傳遞，每個接手者必須在十秒內改造它再傳出，而且不能重複。", "Steal And Upgrade": "借用再升級", "Pick a neighbor's idea you envy, claim it out loud, then make it visibly better before handing it back improved": "挑選旁人一個讓你羨慕的點子，公開借用，明確改進後再交還。", "Fold The Paper": "摺紙接龍", "Each person adds one line to a hidden drawing or sentence, sees only the previous fragment, then unfold the surreal whole": "每人只看前一小段，為隱藏的圖畫或句子增添一筆，最後展開超現實的完整成果。", "Proven & Professional": "經典專業方法", "Structured": "結構化思考", "Deep": "深度探索", "Creative": "創意發想", "Biomimetic": "仿生靈感", "Cultural": "文化啟發", "Speculative Future": "未來想像", "Quantum": "量子隱喻", "Wild": "狂野發想", "Absurdist": "荒誕創意", "Theatrical": "戲劇演繹", "Constraint": "限制挑戰", "Introspective Delight": "內省探索", "Collaborative": "協作共創", "Introspective & Personal": "內省與個人成長", "Build a feature": "開發功能", "Novel concept": "新穎概念", "Strategy": "策略", "Planning": "規劃", "Diagnose": "問題診斷", "Personal / life": "個人／生活", "Get unstuck": "突破卡關", "✨ Invent a Proven & Professional technique": "✨ 自創「經典專業方法」技巧", "Make up a brand-new technique on the fly, in the spirit of Proven & Professional": "依照「經典專業方法」的精神，即興創造一種全新的技巧。", "✨ Invent a Structured technique": "✨ 自創「結構化思考」技巧", "Make up a brand-new technique on the fly, in the spirit of Structured": "依照「結構化思考」的精神，即興創造一種全新的技巧。", "✨ Invent a Deep technique": "✨ 自創「深度探索」技巧", "Make up a brand-new technique on the fly, in the spirit of Deep": "依照「深度探索」的精神，即興創造一種全新的技巧。", "✨ Invent a Creative technique": "✨ 自創「創意發想」技巧", "Make up a brand-new technique on the fly, in the spirit of Creative": "依照「創意發想」的精神，即興創造一種全新的技巧。", "✨ Invent a Biomimetic technique": "✨ 自創「仿生靈感」技巧", "Make up a brand-new technique on the fly, in the spirit of Biomimetic": "依照「仿生靈感」的精神，即興創造一種全新的技巧。", "✨ Invent a Cultural technique": "✨ 自創「文化啟發」技巧", "Make up a brand-new technique on the fly, in the spirit of Cultural": "依照「文化啟發」的精神，即興創造一種全新的技巧。", "✨ Invent a Speculative Future technique": "✨ 自創「未來想像」技巧", "Make up a brand-new technique on the fly, in the spirit of Speculative Future": "依照「未來想像」的精神，即興創造一種全新的技巧。", "✨ Invent a Quantum technique": "✨ 自創「量子隱喻」技巧", "Make up a brand-new technique on the fly, in the spirit of Quantum": "依照「量子隱喻」的精神，即興創造一種全新的技巧。", "✨ Invent a Wild technique": "✨ 自創「狂野發想」技巧", "Make up a brand-new technique on the fly, in the spirit of Wild": "依照「狂野發想」的精神，即興創造一種全新的技巧。", "✨ Invent a Absurdist technique": "✨ 自創「荒誕創意」技巧", "Make up a brand-new technique on the fly, in the spirit of Absurdist": "依照「荒誕創意」的精神，即興創造一種全新的技巧。", "✨ Invent a Theatrical technique": "✨ 自創「戲劇演繹」技巧", "Make up a brand-new technique on the fly, in the spirit of Theatrical": "依照「戲劇演繹」的精神，即興創造一種全新的技巧。", "✨ Invent a Constraint technique": "✨ 自創「限制挑戰」技巧", "Make up a brand-new technique on the fly, in the spirit of Constraint": "依照「限制挑戰」的精神，即興創造一種全新的技巧。", "✨ Invent a Introspective Delight technique": "✨ 自創「內省探索」技巧", "Make up a brand-new technique on the fly, in the spirit of Introspective Delight": "依照「內省探索」的精神，即興創造一種全新的技巧。", "✨ Invent a Collaborative technique": "✨ 自創「協作共創」技巧", "Make up a brand-new technique on the fly, in the spirit of Collaborative": "依照「協作共創」的精神，即興創造一種全新的技巧。", "✨ Invent a Introspective & Personal technique": "✨ 自創「內省與個人成長」技巧", "Make up a brand-new technique on the fly, in the spirit of Introspective & Personal": "依照「內省與個人成長」的精神，即興創造一種全新的技巧。", "BMad Method Brainstorming Selection": "BMad Method 腦力激盪技巧選擇器", "Facilitation": "引導方式", "Facilitator": "引導者", "Creative Partner": "創意夥伴", "Ideate for me": "替我發想", "Techniques": "發想技巧", "Picked ": "已選 ", "Random ": "隨機 ", "Invent ": "自創 ", "AI picks ": "AI 挑選 ", "Copy prompt": "複製提示詞", "Great for": "適用目標", "Jump to": "跳至分類", "BMad Method · Brainstorming": "BMad Method · 腦力激盪", "Total 0 · 3–4 is the sweet spot": "共 0 項 · 建議選擇 3–4 項", "✓ Copied! Now paste it into the chat to start your session.": "✓ 已複製！請貼回聊天室，開始腦力激盪。", "Compose your session, hit ": "設定你的腦力激盪活動，按下 ", ", and paste it back into the chat to begin. 108 techniques across 13 categories.": "，再貼回聊天室即可開始。共 13 類、108 種技巧。"};
  function tr(s){ return ZH[s] || s; }
  var $ = function(id){ return document.getElementById(id); };
  var all = Array.prototype.slice;
  var boxes = all.call(document.querySelectorAll('input[type=checkbox]'));
  var techBoxes = boxes.filter(function(b){ return b.dataset.name; });      // real technique cards
  var inventBoxes = boxes.filter(function(b){ return b.dataset.invent; });  // per-category "invent in the spirit of" cards
  var header = document.querySelector('header');
  var sections = all.call(document.querySelectorAll('section'));
  var state = { mode: 'Facilitator', rand: 0, inv: 0, ai: 0 };
  var MODE_HINTS = {
    'Facilitator': '透過提問與挑戰激發你的想法，由你提出點子。',
    'Creative Partner': '我們一起激盪創意；我負責引導並提出點子，分別標記你的與我的想法。',
    'Ideate for me': '由我完成整場發想，再展示成果，並詢問你是否繼續。'
  };
  function setHint(){ $('modehint').textContent = MODE_HINTS[state.mode] || ''; }

  var themeBtn = $('theme');
  function setThemeIcon(){ themeBtn.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? '☀' : '☾'; }
  themeBtn.addEventListener('click', function(){
    var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('bmad-theme', next); } catch(e){}
    setThemeIcon();
  });

  all.call(document.querySelectorAll('.mode')).forEach(function(b){
    b.addEventListener('click', function(){
      all.call(document.querySelectorAll('.mode')).forEach(function(m){ m.classList.remove('on'); });
      b.classList.add('on');
      state.mode = b.dataset.mode;
      setHint();
    });
  });

  all.call(document.querySelectorAll('[data-step]')).forEach(function(btn){
    btn.addEventListener('click', function(){
      var k = btn.dataset.step, d = parseInt(btn.dataset.d, 10);
      state[k] = Math.max(0, state[k] + d);
      update();
    });
  });

  // Category chips are jump-nav: click one to smooth-scroll its section into view,
  // offsetting by the sticky header's height so the heading isn't hidden beneath it.
  all.call(document.querySelectorAll('.chip')).forEach(function(chip){
    chip.addEventListener('click', function(){
      var sec = null;
      for (var i = 0; i < sections.length; i++){ if (sections[i].dataset.cat === chip.dataset.cat){ sec = sections[i]; break; } }
      if (!sec){ return; }
      var top = sec.getBoundingClientRect().top + window.pageYOffset - header.offsetHeight - 8;
      window.scrollTo({ top: top, behavior: 'smooth' });
    });
  });

  boxes.forEach(function(b){ b.addEventListener('change', update); });

  // A `classic` technique appears twice (lead "Proven & Professional" group + its home
  // category), so de-dupe checked picks by name; the lead copy carries data-lead.
  function checkedTech(){
    var seen = {}, out = [];
    techBoxes.forEach(function(b){
      if (!b.checked || seen[b.dataset.name]) { return; }
      seen[b.dataset.name] = 1;
      out.push(b);
    });
    return out;
  }
  function checkedInvent(){ return inventBoxes.filter(function(b){ return b.checked; }); }

  function update(){
    // rand can't exceed what the pool can supply — keep the counter honest with the draw
    if (state.rand > randomPool().length){ state.rand = randomPool().length; }
    $('pickN').textContent = checkedTech().length;
    $('randN').textContent = state.rand;
    $('invN').textContent = state.inv;
    $('aiN').textContent = state.ai;
    var total = checkedTech().length + state.rand + state.inv + checkedInvent().length + state.ai;
    var t = $('total');
    t.textContent = '共 ' + total + ' 項 · 建議選擇 3–4 項';
    t.classList.toggle('warn', total > 5);
  }

  // "Great for" goal filter: clicking a goal narrows visible cards to those tagged with it.
  var goalBtns = all.call(document.querySelectorAll('.goal'));
  function activeGoals(){ return goalBtns.filter(function(b){ return b.classList.contains('on'); }).map(function(b){ return b.dataset.goal; }); }
  function applyFilter(){
    var act = activeGoals();
    all.call(document.querySelectorAll('label.tech')).forEach(function(lab){
      var inp = lab.querySelector('input');
      if (inp.dataset.invent){ return; }  // invent cards aren't goal-tagged — always visible
      var good = (inp.dataset.good || '').split('|');
      var show = !act.length || act.some(function(g){ return good.indexOf(g) >= 0; });
      lab.classList.toggle('hidden', !show);
    });
  }
  goalBtns.forEach(function(b){ b.addEventListener('click', function(){ b.classList.toggle('on'); applyFilter(); }); });

  function randomPool(){
    var picked = {};
    checkedTech().forEach(function(b){ picked[b.dataset.name] = 1; });
    // draw from unchecked, non-lead copies, skipping anything already picked
    return techBoxes.filter(function(b){ return !b.checked && !b.dataset.lead && !picked[b.dataset.name]; });
  }

  function sample(arr, n){
    var a = arr.slice(), out = [];
    while (out.length < n && a.length){ out.push(a.splice(Math.floor(Math.random() * a.length), 1)[0]); }
    return out;
  }

  function compose(){
    var picks = checkedTech().map(function(b){ return { n: b.dataset.name, c: b.dataset.cat, d: b.dataset.desc, r: false }; });
    var rnd = sample(randomPool(), state.rand).map(function(b){ return { n: b.dataset.name, c: b.dataset.cat, d: b.dataset.desc, r: true }; });
    var techs = picks.concat(rnd);
    var L = ["請開始我的腦力激盪活動，並全程使用繁體中文。", "", '引導模式：' + tr(state.mode) + '。'];
    if (techs.length){
      L.push("", '使用以下技巧：');
      techs.forEach(function(t, i){
        L.push((i + 1) + '.' + (t.r ? '（隨機挑選）' : '') + ' ' + tr(t.n) + '  ·  ' + tr(t.c) + ' [' + t.n + ']');
        L.push('   ' + tr(t.d));
      });
    }
    var extra = [];
    if (state.inv > 0){ extra.push('即興自創 ' + state.inv + ' 種全新技巧'); }
    checkedInvent().forEach(function(b){ extra.push('依照「' + tr(b.dataset.invent) + '」的精神自創 1 種技巧'); });
    if (state.ai > 0){ extra.push('請再挑選 ' + state.ai + ' 種符合我目標的技巧'); }
    if (extra.length){ L.push("", '接著：' + extra.join('；並且') + '。'); }
    if (!techs.length && !extra.length){
      L.push("", state.mode === 'Ideate for me'
        ? '請自行完成整場活動：挑選技巧、產生點子，再展示成果。'
        : '請先協助我挑選 3–4 種技巧。');
    }
    return L.join('\n');
  }

  function fallbackCopy(t){
    var ta = document.createElement('textarea');
    ta.value = t; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.focus(); ta.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch(e){ ok = false; }
    document.body.removeChild(ta);
    return ok;
  }

  function flash(ok, text){
    var b = $('banner');
    b.classList.toggle('fail', !ok);
    b.innerHTML = ok
      ? '✓ 已複製！請貼回聊天室，開始腦力激盪。'
      : '⚠ 無法存取剪貼簿，請複製對話框中的文字，再貼回聊天室。';
    b.classList.add('show');
    setTimeout(function(){ b.classList.remove('show'); }, 4500);
    // Last resort on a hard failure: a prefilled, selectable prompt so the text is never lost.
    if (!ok){ window.prompt('請複製以下文字，再貼回聊天室：', text); }
  }

  $('copy').addEventListener('click', function(){
    var text = compose();
    if (navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(text).then(
        function(){ flash(true, text); },
        function(){ flash(fallbackCopy(text), text); }
      );
    } else { flash(fallbackCopy(text), text); }
  });

  setHint();
  setThemeIcon();
  update();
})();
