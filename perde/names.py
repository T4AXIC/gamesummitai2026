"""Name lexicon for the offline person-name detector.

FIRST_NAMES: common Azerbaijani first names (Latin script), plus frequent
Russian-script forms seen in AZ/RU mixed text. Stored lower-case.
NAME_STOPWORDS: ordinary words that look like surnames by suffix.
"""

_AZ_MALE = """
əli vəli məmməd mehmet məhəmməd hüseyn həsən rəşad elçin elnur elvin elşən elmar elmir
orxan tural tural kamran ramil rauf ruslan rüstəm səməd samir seymur fərid fuad famil
anar aqil akif arif asif azər babək bəhram cavid ceyhun cəlil cavanşir emil eldar elxan
emin elşad faiq fərhad firudin habil heydər ilham ilqar ilkin isa ismayıl iqbal kənan
kamal kərim mahir mirzə müşfiq nadir namiq natiq nicat nihad niyaz nurlan nəsimi oqtay
orxan pərviz rafael rahib rasim rəhim rəsul rövşən sabir sadiq sahib salman sərxan
sənan şahin şamil şəmsi tahir taleh teymur tofiq toğrul ülvi vaqif vüqar vüsal xəyal
yaşar yusif zaur zakir zamiq zeynal ziya cəmil coşqun cahid cəfər əbülfəz ənvər etibar
fazil fikrət hikmət hafiz hacı ibrahim kazım lətif mübariz musa nəriman novruz nizami
qabil qasım qurban rəfael rizvan sabit sərdar sevindik şahmar talıb tələt telman turan
ümid üzeyir vahid valeh vasif vidadi yaqub zahid zöhrab əhməd ağa ayxan aydın ayaz
"""

_AZ_FEMALE = """
aygün aysel aynur ayşən aytən aynurə arzu aidə aida afaq almaz amalya bənövşə dilarə
dilbər dürdanə elmira elnarə elvira esmira fatimə fidan firuzə gülnar gülnarə günay
gülşən gültəkin gülər həcər hicran ilahə jalə jalə kəmalə könül lalə laləzar leyla
lamiyə mehriban mələk mədinə nailə nərmin nigar nərgiz nurlana nuranə pərvanə rəna
rəhilə rüxsarə samirə sevda sevinc sevil sima solmaz südabə şəbnəm şəfəq şəlalə təranə
türkan ülviyyə ülkər vüsalə xədicə yeganə zemfira zərifə zəhra zülfiyyə aybəniz aytac
aynişan ləman lətafət məryəm nəzrin nüray pəri rəşidə sona səbinə səadət şahnaz tamilla
tünzalə ulduz vəfa zeynəb zümrüd günel günel kamilə naznin nərgiz səidə fəridə gülay
"""

_RU = """
иван алексей сергей андрей дмитрий михаил николай владимир ольга елена наталья татьяна
ирина анна мария светлана юлия екатерина анар эльчин рашад орхан турал ильхам айгюн
лейла нигяр севиндж гюнай фарид руслан самир камран эльвин
"""

from pathlib import Path

_FOLD = str.maketrans({"ə": "a", "ü": "u", "ö": "o", "ı": "i", "ş": "s", "ç": "c", "ğ": "g"})


def az_lower(s: str) -> str:
    """Lower-case with Azerbaijani/Turkish dotted and dotless I handled correctly."""
    return s.replace("İ", "i").replace("I", "ı").lower()


def fold(s: str) -> str:
    """ASCII-ish form, so 'Gunay' and 'Mammadli' match 'Günay' and 'Məmmədli'."""
    return az_lower(s).translate(_FOLD).replace("sh", "s").replace("ch", "c")


def _load_lexicon() -> tuple[set[str], set[str]]:
    given, surnames = set(), set()
    path = Path(__file__).with_name("lexicon.txt")
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            kind, _, name = line.partition(" ")
            (given if kind == "G" else surnames).add(name)
    return given, surnames


_LEX_GIVEN, _LEX_SURNAMES = _load_lexicon()

NAME_STOPWORDS = frozenset(
    """
    hörmətli azərbaycanlı bakılı təcili məlumatlı lazımlı növbəli kreditli
    müvafiq vacibli sevimli dəyərli əhəmiyyətli rəsmi ödənişli pulsuz
    şəxsli xidməti nəqliyyatlı mərhələli
    готов основ здоров
    """.split()
)

_base = {az_lower(w) for w in (_AZ_MALE + _AZ_FEMALE + _RU).split()} | _LEX_GIVEN
FIRST_NAMES = frozenset((_base | {fold(w) for w in _base}) - NAME_STOPWORDS)
SURNAMES = frozenset((_LEX_SURNAMES | {fold(w) for w in _LEX_SURNAMES}) - NAME_STOPWORDS)
