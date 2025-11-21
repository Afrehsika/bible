import json
from pathlib import Path

twi_file = Path("data/TWI/TWI_bible.json")

def load_json(path):
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_json(twi_file)

# Genesis 1 Translation
genesis_1 = {
    "1": "Mfiase no Onyankopɔn bɔɔ ɔsoro ne asase.",
    "2": "Na asase no so da mpan, na ɛyɛ sakasaka, na sum wɔ ebun no ani, na Onyankopɔn Honhom kyin nsu no ani.",
    "3": "Na Onyankopɔn kae sɛ: Hann mmra! Na hann bae.",
    "4": "Na Onyankopɔn huu hann no sɛ ɛyɛ; na Onyankopɔn paapaae hann no ne sum no mu.",
    "5": "Na Onyankopɔn frɛɛ hann no Ewiia, na sum no, ɔfrɛɛ no Anadwo. Na ɛyɛɛ anwummere, na ɛyɛɛ anɔpa: da a ɛto so baako.",
    "6": "Na Onyankopɔn kae sɛ: Nkyekyɛmu mmra nsu no ntam, na ɛmpaapaae nsu ne nsu mu.",
    "7": "Na Onyankopɔn yɛɛ nkyekyɛmu no, na ɔpaapaae nsu a ɛwɔ nkyekyɛmu no ase ne nsu a ɛwɔ nkyekyɛmu no atifi mu. Na ɛyɛɛ saa.",
    "8": "Na Onyankopɔn frɛɛ nkyekyɛmu no Ɔsoro. Na ɛyɛɛ anwummere, na ɛyɛɛ anɔpa: da a ɛto so abien.",
    "9": "Na Onyankopɔn kae sɛ: Nsu a ɛwɔ ɔsoro ase no nhyiam faako, na asase wesee no mpue. Na ɛyɛɛ saa.",
    "10": "Na Onyankopɔn frɛɛ asase wesee no Asase, na nsu a ahyiam no, ɔfrɛɛ no Po. Na Onyankopɔn huu sɛ ɛyɛ.",
    "11": "Na Onyankopɔn kae sɛ: Asase mmɔ wira ne nhaire a ɛsow aba, ne nnua a ɛsow aba a n'aba wɔ mu, sɛnea wɔn su te, wɔ asase so. Na ɛyɛɛ saa.",
    "12": "Na asase bɔɔ wira ne nhaire a ɛsow aba sɛnea wɔn su te, ne nnua a ɛsow aba a n'aba wɔ mu sɛnea wɔn su te. Na Onyankopɔn huu sɛ ɛyɛ.",
    "13": "Na ɛyɛɛ anwummere, na ɛyɛɛ anɔpa: da a ɛto so abiɛsa.",
    "14": "Na Onyankopɔn kae sɛ: Nhann mmra ɔsoro nkyekyɛmu no mu, na ɛmpaapaae ewiia ne anadwo mu, na ɛnyɛ nsɛnkyerɛnne ne mmere ne nna ne mfe;",
    "15": "na ɛnyɛ nhann wɔ ɔsoro nkyekyɛmu no mu, na ɛnhyerɛn asase so. Na ɛyɛɛ saa.",
    "16": "Na Onyankopɔn yɛɛ nhann akɛse abien no: hann kɛse no sɛ ɛndi ewiia so, ne hann ketewa no sɛ ɛndi anadwo so; ɔyɛɛ nsoromma nso.",
    "17": "Na Onyankopɔn de sisii ɔsoro nkyekyɛmu no mu sɛ ɛnhyerɛn asase so,",
    "18": "na enni ewiia ne anadwo so, na empaapaae hann ne sum mu. Na Onyankopɔn huu sɛ ɛyɛ.",
    "19": "Na ɛyɛɛ anwummere, na ɛyɛɛ anɔpa: da a ɛto so anan.",
    "20": "Na Onyankopɔn kae sɛ: Nsu no mmɔ mmoa a wɔte ase pii, na ntɛkaa ntu asase so wɔ ɔsoro nkyekyɛmu no ani.",
    "21": "Na Onyankopɔn bɔɔ akɛseɛ akɛse ne mmoa a wɔte ase a wɔwea nyinaa, a nsu no bɔɔ wɔn pii sɛnea wɔn su te, ne ntɛkaa a wɔwɔ ntaban nyinaa sɛnea wɔn su te. Na Onyankopɔn huu sɛ ɛyɛ.",
    "22": "Na Onyankopɔn hyiraa wɔn sɛ: Monwo na monnɔɔso, na monhyɛ po nsu mu ma, na ntɛkaa nnɔɔso asase so.",
    "23": "Na ɛyɛɛ anwummere, na ɛyɛɛ anɔpa: da a ɛto so anum.",
    "24": "Na Onyankopɔn kae sɛ: Asase mmɔ mmoa a wɔte ase sɛnea wɔn su te: anantwi ne mmoa a wɔwea ne asase so mmoa sɛnea wɔn su te. Na ɛyɛɛ saa.",
    "25": "Na Onyankopɔn yɛɛ asase so mmoa sɛnea wɔn su te, ne anantwi sɛnea wɔn su te, ne mmoa a wɔwea asase so nyinaa sɛnea wɔn su te. Na Onyankopɔn huu sɛ ɛyɛ.",
    "26": "Na Onyankopɔn kae sɛ: Momma yɛnyɛ onipa wɔ yɛn suban so, sɛ yɛn sɛso; na wonni po mu mpataa ne ɔsoro ntɛkaa ne anantwi ne asase nyinaa ne mmoa a wɔwea asase so nyinaa so.",
    "27": "Na Onyankopɔn bɔɔ onipa wɔ ne suban so; Onyankopɔn suban so na ɔbɔɔ no; ɔbarima ne ɔbea na ɔbɔɔ wɔn.",
    "28": "Na Onyankopɔn hyiraa wɔn, na Onyankopɔn ka kyerɛɛ wɔn sɛ: Monwo na monnɔɔso, na monhyɛ asase so ma, na monhyɛ so; na monni po mu mpataa ne ɔsoro ntɛkaa ne mmoa a wɔte ase a wɔwea asase so nyinaa so.",
    "29": "Na Onyankopɔn kae sɛ: Hwɛ, mama mo nhaire a ɛsow aba a ɛwɔ asase nyinaa ani, ne nnua nyinaa a eduaba a ɛsow aba wɔ so: ɛnyɛ aduan mma mo.",
    "30": "Na asase so mmoa nyinaa ne ɔsoro ntɛkaa nyinaa ne biribiara a ɛwea asase so a nkwa wɔ mu no, mama wɔn nhaire a ɛyɛ frɔmfrɔm nyinaa sɛ aduan. Na ɛyɛɛ saa.",
    "31": "Na Onyankopɔn huu nea ɔyɛe nyinaa, na hwɛ, ɛyɛ papa. Na ɛyɛɛ anwummere, na ɛyɛɛ anɔpa: da a ɛto so asia."
}

if "Genesis" not in data:
    data["Genesis"] = {}
data["Genesis"]["1"] = genesis_1

save_json(twi_file, data)
print("Updated Genesis 1 in TWI_bible.json")
