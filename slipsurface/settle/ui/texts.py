"""Text of the desktop interface, in English and Turkish.

Whatever the analysis core already says (`slipsurface.settle.i18n`) is reused
under its own key; only what the desktop shell adds is written here, once,
as ``key: (English, Turkish)``.
"""

from __future__ import annotations

from ..i18n import TRANSLATIONS
from ..strings import SHELL

#: key -> (English, Turkish)
UI = {
    # menus
    "m_file": ("&File", "&Dosya"),
    "m_analysis": ("&Analysis", "&Analiz"),
    "m_view": ("&View", "&Görünüm"),
    "m_help": ("&Help", "&Yardım"),
    "m_examples": ("Examples", "Örnekler"),
    "m_report": ("Report", "Rapor"),
    "m_recent": ("Recent projects", "Son projeler"),
    "m_properties": ("&Properties", "Ö&zellikler"),
    "m_language": ("Language / Dil", "Dil / Language"),
    # actions
    "a_new": ("&New", "&Yeni"),
    "a_open": ("&Open…", "&Aç…"),
    "a_save": ("&Save", "&Kaydet"),
    "a_save_as": ("Save &As…", "&Farklı Kaydet…"),
    "a_undo": ("&Undo", "&Geri Al"),
    "a_redo": ("&Redo", "&Yinele"),
    "a_compute": ("&Compute", "&Hesapla"),
    "a_auto": ("Recompute automatically", "Otomatik yeniden hesapla"),
    "a_study": ("Run &study", "Ça&lışmayı başlat"),
    "a_cancel": ("Cancel study", "Çalışmayı iptal et"),
    "a_report": ("Calculation report…", "Hesap raporu…"),
    "a_report_pdf": ("PDF report…", "PDF rapor…"),
    "a_report_html": ("HTML report…", "HTML rapor…"),
    "a_report_docx": ("Word report…", "Word rapor…"),
    "a_export_fig": ("Export figure…", "Şekli dışa aktar…"),
    "a_export_csv": ("Export study table (CSV)…", "Çalışma tablosunu dışa aktar (CSV)…"),
    "a_export_xlsx": ("Export study table (XLSX)…", "Çalışma tablosunu dışa aktar (XLSX)…"),
    "a_dark": ("Dark theme", "Koyu tema"),
    "a_theory": ("Theory manual", "Teori kılavuzu"),
    "a_about": ("About", "Hakkında"),
    "a_quit": ("E&xit", "Çı&kış"),
    "a_materials": ("Define &Materials…", "&Malzemeleri Tanımla…"),
    "a_study_vars": ("Study &Variables…", "Çalışma &Değişkenleri…"),
    "a_add_mat": ("Add material", "Malzeme ekle"),
    "a_copy_mat": ("Copy material", "Malzemeyi kopyala"),
    "a_del_mat": ("Delete material", "Malzemeyi sil"),
    "dlg_materials": ("Define Material Properties", "Malzeme Özelliklerini Tanımla"),
    "dlg_study_vars": ("Study Variables", "Çalışma Değişkenleri"),
    "mat_in_use": (
        "'{name}' is used by {n} layer(s). Give those layers another material first.",
        "'{name}' {n} tabakada kullanılıyor. Önce bu tabakalara başka bir malzeme verin.",
    ),
    "mat_name_empty": ("Every material needs a name.", "Her malzemenin bir adı olmalı."),
    "mat_name_dup": (
        "Two materials are called '{name}'; names must be unique.",
        "İki malzemenin adı '{name}'; adlar benzersiz olmalı.",
    ),
    "btn_ok": ("OK", "Tamam"),
    "btn_cancel": ("Cancel", "İptal"),
    "btn_save": ("Save", "Kaydet"),
    "btn_discard": ("Don't save", "Kaydetme"),
    "mat_empty": (
        "No materials yet. Add one with + below the list.",
        "Henüz malzeme yok. Listenin altındaki + ile ekleyin.",
    ),
    "need_materials": (
        "Define a material first (Properties › Define Materials…).",
        "Önce bir malzeme tanımlayın (Özellikler › Malzemeleri Tanımla…).",
    ),
    "tr_materials": ("Materials", "Malzemeler"),
    "tr_edit_hint": ("Double-click to edit", "Düzenlemek için çift tıklayın"),
    "a_add_row": ("Add layer", "Tabaka ekle"),
    "a_del_row": ("Remove layer", "Tabakayı sil"),
    "a_up": ("Move up", "Yukarı taşı"),
    "a_down": ("Move down", "Aşağı taşı"),
    "a_add_var": ("Add variable", "Değişken ekle"),
    "a_del_var": ("Remove variable", "Değişkeni sil"),
    # workflow steps
    "step_project": ("Project", "Proje"),
    "step_load": ("Foundation / Fill", "Temel / Dolgu"),
    "step_soil": ("Soil Profile", "Zemin Profili"),
    "step_options": ("Options", "Seçenekler"),
    "step_results": ("Results", "Sonuçlar"),
    "step_study": ("Study", "Çalışma"),
    # docks, tabs
    "dock_project": ("Project", "Proje"),
    "dock_tables": ("Tables", "Tablolar"),
    "tab_summary": ("Summary", "Özet"),
    "tab_text": ("Results", "Sonuçlar"),
    "tab_figures": ("Figures", "Şekiller"),
    "tab_study": ("Study", "Çalışma"),
    "tab_soil": ("Soil profile", "Zemin profili"),
    "tab_vars": ("Study variables", "Çalışma değişkenleri"),
    "tab_study_text": ("Summary", "Özet"),
    "tab_study_table": ("Samples", "Örnekler"),
    "inputs": ("Inputs", "Girdiler"),
    "navigator": ("Project tree", "Proje ağacı"),
    # tree
    "tr_water": ("Water table", "Su tablası"),
    "tr_layers": ("Soil layers", "Zemin tabakaları"),
    "tr_results": ("Results", "Sonuçlar"),
    "tr_figures": ("Figures", "Şekiller"),
    "tr_study": ("Study", "Çalışma"),
    "tr_vars": ("{n} variables", "{n} değişken"),
    "tr_samples": ("{n} samples", "{n} örnek"),
    "tr_no_results": ("not computed", "hesaplanmadı"),
    # pages
    "soil_page": (
        "The layers are edited in the Soil profile table below the drawing. "
        "Columns that do not apply to a layer's behaviour are shaded.",
        "Tabakalar çizimin altındaki Zemin profili tablosunda düzenlenir. "
        "Tabakanın davranışına uymayan sütunlar gölgelidir.",
    ),
    "results_page": (
        "The results follow every change of the inputs while automatic "
        "recomputation is on. Pick an item to open its view.",
        "Otomatik yeniden hesap açıkken sonuçlar girdilerdeki her değişikliği "
        "izler. Görünümünü açmak için bir öğe seçin.",
    ),
    "study_vars_page": (
        "The variables are defined in the Study variables table below the drawing.",
        "Değişkenler çizimin altındaki Çalışma değişkenleri tablosunda tanımlanır.",
    ),
    "view": ("View", "Görünüm"),
    "output": ("Output", "Çıktı"),
    # status, messages
    "ready": ("Ready.", "Hazır."),
    "computed": ("Computed in {ms:.0f} ms.", "{ms:.0f} ms'de hesaplandı."),
    "input_error": ("Input error", "Girdi hatası"),
    "stale": (
        "The results do not match the inputs — press Compute (F5).",
        "Sonuçlar girdilerle uyuşmuyor — Hesapla'ya (F5) basın.",
    ),
    "unsaved_title": ("Unsaved changes", "Kaydedilmemiş değişiklikler"),
    "unsaved_text": (
        "The project has unsaved changes. Save them?",
        "Projede kaydedilmemiş değişiklikler var. Kaydedilsin mi?",
    ),
    "untitled": ("Untitled", "Adsız"),
    "file_filter": (
        "SlipSurfaceIQ Settle project (*.settle *.json)",
        "SlipSurfaceIQ Settle projesi (*.settle *.json)",
    ),
    "saved_to": ("Saved: {path}", "Kaydedildi: {path}"),
    "opened": ("Opened: {path}", "Açıldı: {path}"),
    "written": ("Written: {path}", "Yazıldı: {path}"),
    "open_failed": ("Could not open the project", "Proje açılamadı"),
    "save_failed": ("Could not save", "Kaydedilemedi"),
    "report_failed": ("Could not write the report", "Rapor yazılamadı"),
    "need_results": ("Compute the analysis first.", "Önce analizi hesaplayın."),
    "study_running": ("Study running…", "Çalışma sürüyor…"),
    "study_stale": (
        "The study belongs to earlier inputs; run it again.",
        "Çalışma önceki girdilere ait; yeniden başlatın.",
    ),
    "restart_lang": ("Language changed.", "Dil değiştirildi."),
    "no_figure": ("No figure to export.", "Dışa aktarılacak şekil yok."),
    "docx_missing": (
        "Word reports need the python-docx package.",
        "Word raporu için python-docx paketi gerekir.",
    ),
    "xlsx_missing": (
        "The XLSX export needs the openpyxl package.",
        "XLSX dışa aktarımı için openpyxl paketi gerekir.",
    ),
    "about_sub": (
        "Settlement of shallow foundations and embankments",
        "Sığ temellerin ve dolguların oturma analizi",
    ),
    "ex_raft": ("Raft on soft clay", "Yumuşak kil üzerinde radye"),
    "ex_strip": ("Strip footing on sand (Schmertmann)", "Kum üzerinde şerit temel (Schmertmann)"),
    "ex_embankment": ("Embankment on soft clay", "Yumuşak kil üzerinde dolgu"),
    "ex_circle": ("Circular tank on layered clay", "Katmanlı kil üzerinde dairesel tank"),
}


_language = "tr"


def set_language(lang: str) -> None:
    global _language
    _language = lang if lang in ("en", "tr") else "tr"


def language() -> str:
    return _language


def t(key: str, **params) -> str:
    """The text of `key` in the current language, formatted with `params`."""
    if key in UI:
        text = UI[key][1 if _language == "tr" else 0]
    elif key in SHELL:
        text = SHELL[key][1 if _language == "tr" else 0]
    else:
        text = TRANSLATIONS.get(_language, TRANSLATIONS["en"]).get(key, key)
    return text.format(**params) if params else text


def core() -> dict:
    """The analysis core's translations in the current language."""
    return TRANSLATIONS.get(_language, TRANSLATIONS["en"])
