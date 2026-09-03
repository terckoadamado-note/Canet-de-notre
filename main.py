# -*- coding: utf-8 -*-
"""Canet de notre - APK Android.

Interface Kivy légère autour du moteur.py existant. Le moteur est embarqué
et la sauvegarde est faite dans le répertoire privé de l'application.
"""
import os
from decimal import Decimal, InvalidOperation

from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from moteur import MoteurCarnet, Note

BLUE = (0.08, 0.39, 0.75, 1)
BLUE_DARK = (0.04, 0.27, 0.55, 1)
BLUE_LIGHT = (0.91, 0.96, 1, 1)
WHITE = (1, 1, 1, 1)
TEXT = (0.08, 0.12, 0.18, 1)
MUTED = (0.42, 0.47, 0.55, 1)
RED = (0.85, 0.05, 0.05, 1)
RED_LIGHT = (1, 0.88, 0.88, 1)
GREEN = (0.05, 0.55, 0.25, 1)
GREEN_LIGHT = (0.88, 0.97, 0.90, 1)
BORDER = (0.72, 0.78, 0.86, 1)

COMMON_SUBJECTS = [
    "Mathématiques", "Français", "Anglais", "Histoire-Géographie",
    "SVT", "Physique-Chimie", "PCT", "Informatique",
    "Éducation Physique et Sportive", "Philosophie", "Économie",
    "Allemand", "Espagnol", "Éducation Civique et Morale",
    "Arts Plastiques", "Musique", "Technologie"
]


def solid(widget, color, radius=0):
    with widget.canvas.before:
        Color(*color)
        if radius:
            from kivy.graphics import RoundedRectangle
            widget._bg = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])
        else:
            widget._bg = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda *_: setattr(widget._bg, 'pos', widget.pos),
                size=lambda *_: setattr(widget._bg, 'size', widget.size))
    return widget


class NoteInput(TextInput):
    def __init__(self, app_ref, matiere_index, kind, note_index, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app_ref
        self.matiere_index = matiere_index
        self.kind = kind
        self.note_index = note_index
        self.multiline = False
        self.input_filter = 'float'
        self.halign = 'center'
        self.font_size = dp(15)
        self.padding = [dp(2), dp(8), dp(2), dp(0)]
        self.background_normal = ''
        self.background_color = WHITE
        self.foreground_color = TEXT
        self.bind(focus=self._focus_changed)
        self.bind(text=self._text_changed)
        self._last_touch_time = 0

    def _focus_changed(self, _, focused):
        if not focused:
            self.text = self.text.replace(',', '.')
            self.app_ref.set_note(self.matiere_index, self.kind, self.note_index, self.text)

    def _text_changed(self, *_):
        # La saisie ne déclenche jamais un recalcul.
        pass

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.is_double_tap:
            self.app_ref.open_bareme(self.matiere_index, self.kind, self.note_index)
            return True
        return super().on_touch_down(touch)


class PieChart(Widget):
    data = []
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []
        self.bind(size=self.redraw, pos=self.redraw)

    def set_data(self, data):
        self.data = data or []
        self.redraw()

    def redraw(self, *_):
        self.canvas.clear()
        if not self.data:
            return
        total = sum(float(max(v, 0)) for _, v in self.data)
        if total <= 0:
            return
        cx = self.center_x
        cy = self.center_y
        r = min(self.width, self.height) * 0.38
        angle = 0
        palette = [
            (0.10,0.39,0.80,1),(0.12,0.65,0.52,1),(0.95,0.61,0.12,1),
            (0.55,0.30,0.78,1),(0.86,0.25,0.25,1),(0.20,0.62,0.85,1),
            (0.30,0.75,0.30,1),(0.65,0.45,0.20,1)
        ]
        for i, (_, value) in enumerate(self.data):
            extent = 360 * float(max(value, 0)) / total
            Color(*palette[i % len(palette)])
            Ellipse(pos=(cx-r, cy-r), size=(2*r, 2*r), angle_start=angle, angle_end=angle+extent)
            angle += extent
        Color(*WHITE)
        Ellipse(pos=(cx-r*0.46, cy-r*0.46), size=(0.92*r, 0.92*r))


class CanetApp(App):
    title = "Canet de notre"
    current_semester = 1
    drawer_open = BooleanProperty(False)
    drawer_width = NumericProperty(0)

    def build(self):
        Window.clearcolor = BLUE_LIGHT
        self.data_path = os.path.join(self.user_data_dir, 'carnet_donnees.json')
        self.settings_path = os.path.join(self.user_data_dir, 'parametres.json')
        self.moteur = MoteurCarnet(self.data_path)
        self.moteur.charger()
        self.load_settings()
        self.last_result = None
        self.root = FloatLayout()
        self.main_layout = BoxLayout(orientation='vertical', size_hint=(1,1))
        self.root.add_widget(self.main_layout)
        self.build_main()
        return self.root

    @property
    def semestre(self):
        return self.moteur.annee.premier_semestre if self.current_semester == 1 else self.moteur.annee.deuxieme_semestre

    def load_settings(self):
        import json
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                data=json.load(f)
            if 'bareme_defaut' in data:
                self.moteur.parametres.definir_bareme_defaut(data['bareme_defaut'])
        except Exception:
            pass

    def save_settings(self):
        import json
        with open(self.settings_path, 'w', encoding='utf-8') as f:
            json.dump({'bareme_defaut': float(self.moteur.parametres.bareme_defaut)}, f, ensure_ascii=False, indent=2)

    def build_main(self):
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(self.header())
        self.main_layout.add_widget(self.body())
        self.main_layout.add_widget(self.bottom_nav())
        self.refresh_table()

    def header(self):
        box = BoxLayout(size_hint_y=None, height=dp(70), padding=[dp(10), dp(8)], spacing=dp(8))
        solid(box, BLUE)
        menu = Button(text='☰', size_hint_x=None, width=dp(48), background_normal='', background_color=(1,1,1,0.14), color=WHITE, font_size=dp(26))
        menu.bind(on_release=lambda *_: self.toggle_drawer())
        box.add_widget(menu)
        title = Label(text='📚  CANET DE NOTRE', color=WHITE, bold=True, font_size=dp(20), halign='left', valign='middle')
        title.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
        box.add_widget(title)
        notif = Button(text='🔔', size_hint_x=None, width=dp(48), background_normal='', background_color=(1,1,1,0.14), color=WHITE, font_size=dp(23))
        notif.bind(on_release=lambda *_: self.show_notifications())
        self.notif_button = notif
        box.add_widget(notif)
        more = Button(text='⋮', size_hint_x=None, width=dp(42), background_normal='', background_color=(1,1,1,0.14), color=WHITE, font_size=dp(26))
        more.bind(on_release=lambda *_: self.show_more_menu())
        box.add_widget(more)
        return box

    def body(self):
        outer = BoxLayout(orientation='vertical')
        tabs = BoxLayout(size_hint_y=None, height=dp(48), padding=dp(6), spacing=dp(6))
        for num, label in [(1,'Premier semestre'), (2,'Deuxième semestre')]:
            b = Button(text=label, background_normal='', background_color=BLUE if self.current_semester == num else WHITE, color=WHITE if self.current_semester == num else TEXT, bold=True)
            b.bind(on_release=lambda btn, n=num: self.switch_semester(n))
            tabs.add_widget(b)
        annual = Button(text='Moyenne annuelle', background_normal='', background_color=WHITE, color=TEXT, bold=True)
        annual.bind(on_release=lambda *_: self.show_annual())
        tabs.add_widget(annual)
        outer.add_widget(tabs)

        scroll = ScrollView(do_scroll_x=True, do_scroll_y=True)
        self.table_holder = BoxLayout(orientation='vertical', size_hint=(None, None), padding=dp(8))
        self.table_holder.bind(minimum_width=self.table_holder.setter('width'), minimum_height=self.table_holder.setter('height'))
        scroll.add_widget(self.table_holder)
        outer.add_widget(scroll)
        return outer

    def bottom_nav(self):
        bar = BoxLayout(size_hint_y=None, height=dp(70), padding=[dp(8), dp(6)], spacing=dp(8))
        solid(bar, WHITE)
        home = Button(text='⌂\nAccueil', background_normal='', background_color=BLUE_LIGHT, color=BLUE_DARK, bold=True)
        stats = Button(text='◉\nStatistiques', size_hint_x=1.25, background_normal='', background_color=BLUE, color=WHITE, bold=True, font_size=dp(15))
        save = Button(text='💾\nSauvegarde', background_normal='', background_color=BLUE_LIGHT, color=BLUE_DARK, bold=True)
        home.bind(on_release=lambda *_: self.build_main())
        stats.bind(on_release=lambda *_: self.show_statistics())
        save.bind(on_release=lambda *_: self.save_now())
        bar.add_widget(home); bar.add_widget(stats); bar.add_widget(save)
        return bar

    def refresh_table(self):
        if not hasattr(self, 'table_holder'):
            return
        self.table_holder.clear_widgets()
        sem = self.semestre
        max_i = max([len(m.interrogations) for m in sem.matieres] or [1])
        max_d = max([len(m.devoirs) for m in sem.matieres] or [1])
        subject_w, coef_w, note_w, mean_w, trash_w = dp(150), dp(62), dp(58), dp(75), dp(48)
        table_w = subject_w + coef_w + (max_i + max_d) * note_w + mean_w + trash_w

        title = Label(text='TABLEAU DE NOTES', size_hint=(None,None), size=(dp(220),dp(42)), color=BLUE_DARK, bold=True, font_size=dp(22))
        self.table_holder.add_widget(title)

        # Niveau 1 : en-tête hiérarchique avec groupes réellement regroupés.
        row1 = BoxLayout(orientation='horizontal', size_hint=(None,None), size=(table_w,dp(42)), spacing=dp(1))
        for txt,w in [('Matière',subject_w),('Coef',coef_w)]: row1.add_widget(self.cell(txt,w,BLUE,WHITE,True))
        row1.add_widget(self.cell('INTERROGATIONS', max_i*note_w, BLUE, WHITE, True))
        row1.add_widget(self.cell('DEVOIRS', max_d*note_w, BLUE, WHITE, True))
        row1.add_widget(self.cell('Moyenne', mean_w, BLUE, WHITE, True))
        row1.add_widget(self.cell('🗑', trash_w, BLUE, WHITE, True))
        self.table_holder.add_widget(row1)

        # Niveau 2 : I1...In / D1...Dn.
        row2 = BoxLayout(orientation='horizontal', size_hint=(None,None), size=(table_w,dp(34)), spacing=dp(1))
        row2.add_widget(self.cell('',subject_w,BLUE_DARK,WHITE)); row2.add_widget(self.cell('',coef_w,BLUE_DARK,WHITE))
        for i in range(max_i): row2.add_widget(self.cell(f'I{i+1}',note_w,BLUE_DARK,WHITE,True))
        for i in range(max_d): row2.add_widget(self.cell(f'D{i+1}',note_w,BLUE_DARK,WHITE,True))
        row2.add_widget(self.cell('',mean_w,BLUE_DARK,WHITE)); row2.add_widget(self.cell('',trash_w,BLUE_DARK,WHITE))
        self.table_holder.add_widget(row2)

        if not sem.matieres:
            empty = BoxLayout(orientation='horizontal', size_hint=(None,None), size=(table_w,dp(50)))
            empty.add_widget(self.cell('Aucune matière',subject_w,WHITE,MUTED,True))
            for w in [coef_w]+[note_w]*(max_i+max_d)+[mean_w,trash_w]: empty.add_widget(self.cell('',w,WHITE,TEXT))
            self.table_holder.add_widget(empty)
        else:
            for mi, mat in enumerate(sem.matieres):
                row = BoxLayout(orientation='horizontal', size_hint=(None,None), size=(table_w,dp(50)), spacing=dp(1))
                subject_bg = (0.94,0.94,0.94,1) if mat.nom == 'Matière' else BLUE_LIGHT
                subject = Button(text=mat.nom, size_hint=(None,None), size=(subject_w,dp(50)), background_normal='', background_color=subject_bg, color=MUTED if mat.nom == 'Matière' else TEXT, bold=True)
                subject.bind(on_release=lambda _, i=mi: self.edit_subject(i)); row.add_widget(subject)
                coef = TextInput(text=str(mat.coefficient), size_hint=(None,None), size=(coef_w,dp(50)), multiline=False, input_filter='float', halign='center', background_normal='', background_color=WHITE)
                coef.bind(on_text_validate=lambda w, i=mi: self.set_coefficient(i, w.text)); row.add_widget(coef)
                for ni in range(max_i):
                    if ni < len(mat.interrogations):
                        note=mat.interrogations[ni]; inp=NoteInput(self,mi,'interrogation',ni,text='' if note.valeur is None else str(note.valeur),size_hint=(None,None),size=(note_w,dp(50))); self.style_note_input(inp,note); row.add_widget(inp)
                    else: row.add_widget(self.cell('',note_w,WHITE,TEXT))
                for ni in range(max_d):
                    if ni < len(mat.devoirs):
                        note=mat.devoirs[ni]; inp=NoteInput(self,mi,'devoir',ni,text='' if note.valeur is None else str(note.valeur),size_hint=(None,None),size=(note_w,dp(50))); self.style_note_input(inp,note); row.add_widget(inp)
                    else: row.add_widget(self.cell('',note_w,WHITE,TEXT))
                mean=self.last_result_mean(mi); row.add_widget(self.cell('' if mean is None else self.fmt(mean),mean_w,BLUE_LIGHT,BLUE_DARK,True))
                trash=Button(text='🗑',size_hint=(None,None),size=(trash_w,dp(50)),background_normal='',background_color=RED_LIGHT,color=RED,font_size=dp(18)); trash.bind(on_release=lambda _,i=mi:self.delete_subject(i)); row.add_widget(trash)
                self.table_holder.add_widget(row)
        self.add_summary()
        self.update_notification_badge()

    def cell(self, text, width, bg, fg, bold=False):
        l = Label(text=text, size_hint=(None,None), size=(width,dp(48)), color=fg, bold=bold, halign='center', valign='middle')
        solid(l, bg)
        l.bind(size=lambda w,s: setattr(w,'text_size',s))
        return l

    def style_note_input(self, inp, note):
        if note.valeur is not None and (note.valeur < 0 or note.valeur > note.bareme):
            inp.background_color = RED_LIGHT
            inp.foreground_color = RED
        else:
            inp.background_color = WHITE
            inp.foreground_color = TEXT

    def add_summary(self):
        sem = self.semestre
        total_coef = sum((Decimal(str(m.coefficient)) for m in sem.matieres), Decimal('0'))
        box = GridLayout(cols=3, size_hint=(None,None), width=dp(390), height=dp(75), spacing=dp(6), padding=dp(4))
        box.add_widget(self.cell(f'N matières\n{len(sem.matieres)}', dp(125), WHITE, BLUE_DARK, True))
        box.add_widget(self.cell(f'N coefficients\n{self.fmt(total_coef)}', dp(125), WHITE, BLUE_DARK, True))
        mean = self.current_general_mean()
        box.add_widget(self.cell(f'Moyenne totale\n{self.fmt(mean) if mean is not None else "—"}', dp(125), WHITE, BLUE_DARK, True))
        self.table_holder.add_widget(box)
        self.calc_button = Button(text='CALCULER', size_hint=(None,None), size=(dp(390),dp(54)), background_normal='', background_color=BLUE, color=WHITE, bold=True, font_size=dp(17))
        self.calc_button.bind(on_release=lambda *_: self.calculate())
        self.table_holder.add_widget(self.calc_button)
        self.status_label = Label(text='', size_hint=(None,None), width=dp(390), height=dp(32), color=GREEN, bold=True)
        self.table_holder.add_widget(self.status_label)
        if getattr(self, '_bottom_warning', ''):
            self.show_bottom_warning(self._bottom_warning)

    def fmt(self, value):
        if value is None: return '—'
        try:
            d = Decimal(str(value))
            return str(int(d)) if d == d.to_integral_value() else format(d.normalize(),'f')
        except Exception:
            return str(value)

    def last_result_mean(self, idx):
        if not self.last_result: return None
        for r in self.last_result.get('matieres', []):
            if r.get('matiere') == self.semestre.matieres[idx].nom:
                # La colonne « Moyenne » affiche les points pondérés,
                # c'est-à-dire moyenne de la matière × coefficient.
                return r.get('points')
        return None

    def current_general_mean(self):
        if self.last_result and self.last_result.get('nom') == self.semestre.nom:
            return self.last_result.get('moyenne')
        return None

    def switch_semester(self, n):
        self.current_semester = n
        self.last_result = None
        self.build_main()

    def set_coefficient(self, idx, value):
        try:
            d = Decimal(str(value).replace(',','.'))
            if d <= 0: raise ValueError
            self.semestre.matieres[idx].coefficient = d
            self.moteur.sauvegarder()
            self.last_result = None
        except Exception:
            self.show_error('Coefficient invalide.')
        self.refresh_table()

    def set_note(self, mi, kind, ni, value):
        try:
            note = self.semestre.matieres[mi].interrogations[ni] if kind == 'interrogation' else self.semestre.matieres[mi].devoirs[ni]
            if value.strip() == '': note.valeur = None
            else:
                d = Decimal(value.replace(',','.'))
                if d < 0: raise ValueError('Une note négative est impossible.')
                note.valeur = d
            self.moteur.sauvegarder()
            self.last_result = None
            self._bottom_warning = ''
            self.refresh_table()
        except (InvalidOperation, ValueError):
            self.show_error('La note doit être un nombre positif.')

    def calculate(self):
        # Detect invalid notes before calling the strict engine, preserving the engine unchanged.
        invalid = []
        for m in self.semestre.matieres:
            for kind, notes in [('interrogation', m.interrogations), ('devoir', m.devoirs)]:
                for i, n in enumerate(notes):
                    if n.valeur is not None and (n.valeur < 0 or n.valeur > n.bareme):
                        invalid.append(f'{m.nom} — {kind} {i+1}: {n.valeur} > {n.bareme}')
        if invalid:
            self._bottom_warning = '🔴 Attention : une note dépasse son barème.'
            self.show_bottom_warning(self._bottom_warning)
            return
        try:
            self.last_result = self.moteur.calculer()[self.result_key()]
            self.generate_advice_notifications()
            self.status_label.text = '✓ Calcul effectué'
            self.status_label.color = GREEN
            self._bottom_warning = ''
            self.refresh_table()
            self.status_label.text = '✓ Calcul effectué'
            Clock.schedule_once(lambda *_: self.clear_status(), 3)
        except Exception as e:
            self.show_bottom_warning('🔴 ' + str(e))

    def result_key(self):
        return 'premier_semestre' if self.current_semester == 1 else 'deuxieme_semestre'

    def clear_status(self):
        if hasattr(self, 'status_label'):
            self.status_label.text = ''

    def show_bottom_warning(self, msg):
        self._bottom_warning = msg
        if hasattr(self, 'status_label'):
            self.status_label.text = msg
            self.status_label.color = RED

    def save_now(self):
        try:
            self.moteur.sauvegarder()
            self._bottom_warning = ''
            self.show_bottom_warning('✓ Sauvegarde effectuée')
            self.status_label.color = GREEN
            Clock.schedule_once(lambda *_: self.clear_status(), 3)
        except Exception as e:
            self.show_bottom_warning('🔴 ' + str(e))

    def edit_subject(self, idx):
        self.open_subject_dialog(idx)

    def add_subject(self, name=None, coefficient=1):
        try:
            name = (name or '').strip()
            if not name: raise ValueError('Nom de matière obligatoire.')
            mat = self.semestre.ajouter_matiere(name, Decimal(str(coefficient)))
            default_i = self.moteur.parametres.interrogations_defaut
            default_d = self.moteur.parametres.devoirs_defaut
            default_b = self.moteur.parametres.bareme_defaut
            for _ in range(default_i): mat.ajouter_interrogation(None, default_b)
            for _ in range(default_d): mat.ajouter_devoir(None, default_b)
            self.moteur.sauvegarder(); self.last_result = None; self.refresh_table()
        except Exception as e:
            self.show_error(str(e))

    def delete_subject(self, idx):
        if 0 <= idx < len(self.semestre.matieres):
            self.semestre.matieres.pop(idx)
            self.moteur.sauvegarder(); self.last_result = None; self.refresh_table()

    def add_column(self, kind):
        default_b = self.moteur.parametres.bareme_defaut
        for m in self.semestre.matieres:
            if kind == 'interrogation': m.ajouter_interrogation(None, default_b)
            else: m.ajouter_devoir(None, default_b)
        self.moteur.sauvegarder(); self.refresh_table()

    def delete_column(self, kind):
        for m in self.semestre.matieres:
            if kind == 'interrogation' and m.interrogations: m.interrogations.pop()
            if kind == 'devoir' and m.devoirs: m.devoirs.pop()
        self.moteur.sauvegarder(); self.refresh_table()

    def open_bareme(self, mi, kind, ni):
        note = self.semestre.matieres[mi].interrogations[ni] if kind == 'interrogation' else self.semestre.matieres[mi].devoirs[ni]
        self.simple_dialog('Modifier le barème', str(note.bareme), lambda value: self.set_bareme(mi, kind, ni, value))

    def set_bareme(self, mi, kind, ni, value):
        try:
            b = Decimal(str(value).replace(',','.'))
            if b <= 0: raise ValueError
            note = self.semestre.matieres[mi].interrogations[ni] if kind == 'interrogation' else self.semestre.matieres[mi].devoirs[ni]
            note.bareme = b
            self.moteur.sauvegarder(); self.refresh_table()
        except Exception:
            self.show_error('Barème invalide.')

    def show_more_menu(self):
        content = BoxLayout(orientation='vertical', spacing=dp(6), padding=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        for label, fn in [
            ('＋ Ajouter une matière', self.open_subject_dialog),
            ('＋ Ajouter une interrogation', lambda: self.add_column('interrogation')),
            ('＋ Ajouter un devoir', lambda: self.add_column('devoir')),
            ('− Supprimer une interrogation', lambda: self.delete_column('interrogation')),
            ('− Supprimer un devoir', lambda: self.delete_column('devoir')),
            ('🗑 Supprimer une matière', self.open_delete_subjects),
        ]:
            b=Button(text=label, size_hint_y=None, height=dp(48), background_normal='', background_color=BLUE_LIGHT, color=TEXT, bold=True)
            b.bind(on_release=lambda _, f=fn: (self.close_modal(), f()))
            content.add_widget(b)
        self.open_modal('Actions', content)

    def open_subject_dialog(self, idx=None):
        box=BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(10), size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))
        field=TextInput(hint_text='Matière', multiline=False, size_hint_y=None, height=dp(48), background_normal='', background_color=(0.94,0.94,0.94,1), foreground_color=MUTED)
        box.add_widget(field)
        coef=TextInput(hint_text='Coefficient', text='1', multiline=False, input_filter='float', size_hint_y=None, height=dp(48))
        box.add_widget(coef)
        lab=Label(text='Matières courantes', size_hint_y=None, height=dp(35), color=BLUE_DARK, bold=True)
        box.add_widget(lab)
        sv=ScrollView(size_hint_y=None, height=dp(210))
        lst=GridLayout(cols=1, spacing=dp(5), size_hint_y=None); lst.bind(minimum_height=lst.setter('height'))
        for s in COMMON_SUBJECTS:
            b=Button(text=s, size_hint_y=None, height=dp(40), background_normal='', background_color=BLUE_LIGHT, color=TEXT)
            b.bind(on_release=lambda _, s=s: setattr(field,'text',s))
            lst.add_widget(b)
        sv.add_widget(lst); box.add_widget(sv)
        row=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(6))
        cancel=Button(text='Annuler'); save=Button(text='Ajouter',background_normal='',background_color=BLUE,color=WHITE,bold=True)
        row.add_widget(cancel); row.add_widget(save); box.add_widget(row)
        modal=self.open_modal('Ajouter une matière', box)
        cancel.bind(on_release=lambda *_: self.close_modal())
        save.bind(on_release=lambda *_: (self.close_modal(), self.add_subject(field.text, Decimal(coef.text or '1'))))

    def open_delete_subjects(self):
        box=GridLayout(cols=1, spacing=dp(5), padding=dp(10), size_hint_y=None); box.bind(minimum_height=box.setter('height'))
        for i,m in enumerate(self.semestre.matieres):
            b=Button(text=f'🗑 {m.nom}', size_hint_y=None, height=dp(45), background_normal='', background_color=RED_LIGHT, color=RED)
            b.bind(on_release=lambda _, i=i: (self.close_modal(), self.delete_subject(i)))
            box.add_widget(b)
        self.open_modal('Supprimer une matière', box)

    def show_annual(self):
        result = self.moteur.annee.calculer()
        box=BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(12), size_hint_y=None); box.bind(minimum_height=box.setter('height'))
        for label,key in [('Premier semestre','premier_semestre'),('Deuxième semestre','deuxieme_semestre')]:
            val=result[key]['moyenne']; box.add_widget(Label(text=f'{label} : {self.fmt(val)}', size_hint_y=None,height=dp(42),color=TEXT,bold=True))
        box.add_widget(Label(text=f'Moyenne annuelle : {self.fmt(result["moyenne_annuelle"])}', size_hint_y=None,height=dp(50),color=BLUE_DARK,bold=True,font_size=dp(19)))
        box.add_widget(Label(text='(Premier semestre × 2 + Deuxième semestre) ÷ 3', size_hint_y=None,height=dp(45),color=MUTED))
        close=Button(text='Fermer',size_hint_y=None,height=dp(45),background_normal='',background_color=BLUE,color=WHITE)
        box.add_widget(close); modal=self.open_modal('Moyenne annuelle',box); close.bind(on_release=lambda *_: self.close_modal())

    def show_statistics(self):
        result=self.moteur.annee.calculer()
        sem=result['premier_semestre'] if self.current_semester==1 else result['deuxieme_semestre']
        data=[(r['matiere'], float(r['points'])) for r in sem['matieres'] if r['points'] is not None]
        box=BoxLayout(orientation='vertical',padding=dp(10),spacing=dp(8),size_hint_y=None); box.bind(minimum_height=box.setter('height'))
        chart=PieChart(size_hint=(1,None),height=dp(290)); chart.set_data(data); box.add_widget(chart)
        for name,val in data:
            box.add_widget(Label(text=f'{name} : {self.fmt(val)} points',size_hint_y=None,height=dp(28),color=TEXT))
        close=Button(text='Fermer',size_hint_y=None,height=dp(45),background_normal='',background_color=BLUE,color=WHITE); box.add_widget(close)
        self.open_modal('Statistiques — diagramme circulaire',box); close.bind(on_release=lambda *_: self.close_modal())

    def generate_advice_notifications(self):
        # Conseils seulement lorsque le remplissage est suffisamment avancé
        # (au moins 2/3 des cellules prévues) et après un calcul explicite.
        sem = self.semestre
        total_slots = sum(len(m.interrogations) + len(m.devoirs) for m in sem.matieres)
        filled = sum(1 for m in sem.matieres for n in (m.interrogations + m.devoirs) if n.valeur is not None)
        if total_slots == 0 or filled / total_slots < (2/3):
            return
        result = self.last_result or {}
        mean = result.get('moyenne')
        if mean is not None and Decimal(str(mean)) < Decimal('10') and not any(n.titre == 'Moyenne générale à surveiller' and not n.lue for n in self.moteur.notifications.notifications):
            self.moteur.notifications.ajouter(
                'Moyenne générale à surveiller',
                f'La moyenne actuelle est {self.fmt(mean)}. Consultez les conseils pour identifier les matières à renforcer et viser au moins 10.',
                'attention'
            )
        for r in result.get('matieres', []):
            m = Decimal(str(r.get('moyenne'))) if r.get('moyenne') is not None else None
            if m is not None and m < Decimal('10') and not any(n.titre == f'À travailler : {r.get("matiere", "Matière")}' and not n.lue for n in self.moteur.notifications.notifications):
                self.moteur.notifications.ajouter(
                    f'À travailler : {r.get("matiere", "Matière")}',
                    f'Moyenne actuelle : {self.fmt(m)}. Renforce cette matière pour te rapprocher d’au moins 10.',
                    'attention'
                )

    def show_notifications(self):
        notes=self.moteur.notifications.notifications
        box=BoxLayout(orientation='vertical',spacing=dp(6),padding=dp(10),size_hint_y=None); box.bind(minimum_height=box.setter('height'))
        if not notes: box.add_widget(Label(text='Aucune notification.',size_hint_y=None,height=dp(45),color=MUTED))
        for n in notes:
            box.add_widget(Label(text=f'• {n.titre}\n{n.message}',size_hint_y=None,height=dp(65),color=RED if n.niveau=='erreur' else TEXT))
        close=Button(text='Fermer',size_hint_y=None,height=dp(45),background_normal='',background_color=BLUE,color=WHITE); box.add_widget(close)
        self.open_modal('Notifications',box); close.bind(on_release=lambda *_: self.close_modal())
        self.moteur.notifications.tout_marquer_comme_lu(); self.update_notification_badge()

    def update_notification_badge(self):
        if hasattr(self,'notif_button'):
            count=self.moteur.notifications.nombre_non_lues()
            self.notif_button.text='🔔  🔴' if count else '🔔'

    def toggle_drawer(self):
        if self.drawer_open: self.close_drawer()
        else: self.open_drawer()

    def open_drawer(self):
        if hasattr(self,'drawer'): self.drawer.parent and self.drawer.parent.remove_widget(self.drawer)
        drawer=BoxLayout(orientation='vertical',size_hint=(None,1),width=0,padding=dp(12),spacing=dp(8))
        solid(drawer,WHITE)
        for label,fn in [('🏠 Accueil', self.build_main),('🔔 Notifications', self.show_notifications),('📊 Barèmes', self.show_baremes),('❓ Aide', self.show_help),('ℹ À propos', self.show_about)]:
            b=Button(text=label,size_hint_y=None,height=dp(50),background_normal='',background_color=BLUE_LIGHT,color=TEXT,bold=True)
            b.bind(on_release=lambda _, f=fn: (self.close_drawer(), f()))
            drawer.add_widget(b)
        drawer.add_widget(Label())
        drawer.pos = (0, 0)
        self.drawer=drawer
        self.root.add_widget(drawer)
        self.drawer_open=True
        Animation(width=dp(280),duration=.25,t='out_cubic').start(drawer)

    def close_drawer(self):
        if hasattr(self,'drawer'):
            Animation(width=0,duration=.22,t='in_cubic').start(self.drawer)
        self.drawer_open=False

    def show_baremes(self):
        current=self.moteur.parametres.bareme_defaut
        self.simple_dialog('Barème par défaut', str(current), self.set_default_bareme)

    def set_default_bareme(self,value):
        try:
            self.moteur.parametres.definir_bareme_defaut(value); self.save_settings(); self.moteur.sauvegarder()
        except Exception: self.show_error('Barème invalide.')

    def show_help(self):
        text='''• Les matières sont des lignes.\n• Les interrogations restent dans le groupe INTERROGATIONS.\n• Les devoirs restent dans le groupe DEVOIRS.\n• Barème invisible dans le tableau, 20 par défaut.\n• Double-appui sur une note : modifier son barème.\n• Les cellules de notes acceptent des nombres.\n• Aucun calcul automatique pendant la saisie.\n• CALCULER lance le moteur.\n• Une note hors barème est signalée en rouge en bas.\n• Les conseils utilisent l’indicateur rouge de 🔔.'''
        self.text_modal('Aide',text)

    def show_about(self):
        text='''Cahier de notes\n\nVersion 1.0\n\nAuteur : Jacques Adamado 🤣\n\nNous vous souhaitons une agréable utilisation de l'application.\n\nSi vous rencontrez un problème ou avez une suggestion, vous pouvez le signaler afin de contribuer à l'amélioration des prochaines versions.\n\nFacebook : Fin de l'histoire\n\nTéléphone : +299 01 48 25 66 62\n\nMerci pour votre confiance.'''
        self.text_modal('À propos',text)

    def simple_dialog(self,title,value,callback):
        box=BoxLayout(orientation='vertical',padding=dp(10),spacing=dp(8),size_hint_y=None); box.bind(minimum_height=box.setter('height'))
        field=TextInput(text=value,multiline=False,input_filter='float',size_hint_y=None,height=dp(48))
        box.add_widget(field); row=BoxLayout(size_hint_y=None,height=dp(45),spacing=dp(6)); cancel=Button(text='Annuler'); ok=Button(text='Valider',background_normal='',background_color=BLUE,color=WHITE); row.add_widget(cancel);row.add_widget(ok);box.add_widget(row)
        self.open_modal(title,box); cancel.bind(on_release=lambda *_: self.close_modal()); ok.bind(on_release=lambda *_: (self.close_modal(),callback(field.text)))

    def text_modal(self,title,text):
        box=BoxLayout(orientation='vertical',padding=dp(12),spacing=dp(8),size_hint_y=None); box.bind(minimum_height=box.setter('height'))
        box.add_widget(Label(text=text,size_hint_y=None,height=dp(250),color=TEXT,halign='left',valign='top'))
        b=Button(text='Fermer',size_hint_y=None,height=dp(45),background_normal='',background_color=BLUE,color=WHITE);box.add_widget(b);self.open_modal(title,box);b.bind(on_release=lambda *_: self.close_modal())

    def open_modal(self,title,content):
        self._modal=ModalView(size_hint=(.92,.80),auto_dismiss=False,background_color=(0,0,0,.35))
        wrap=BoxLayout(orientation='vertical',padding=dp(10),spacing=dp(8));solid(wrap,WHITE)
        wrap.add_widget(Label(text=title,size_hint_y=None,height=dp(45),color=BLUE_DARK,bold=True,font_size=dp(20)))
        wrap.add_widget(content);self._modal.add_widget(wrap);self._modal.open();return self._modal

    def close_modal(self):
        if hasattr(self,'_modal') and self._modal:
            self._modal.dismiss(); self._modal=None

    def show_error(self,msg):
        self._bottom_warning='🔴 '+msg
        if hasattr(self,'status_label'):
            self.status_label.text=self._bottom_warning; self.status_label.color=RED


if __name__ == '__main__':
    CanetApp().run()
